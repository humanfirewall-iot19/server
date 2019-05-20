from flask import Flask, send_file, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename

import logging
import face_recognition
import faiss
import random
import string
import time
import bot
import numpy as np
import os

#logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

BASE_URL = "http://134.209.95.86:8080/" if os.getenv("BASE_URL") is None else os.getenv("BASE_URL")
PORT = 5000 if os.getenv("PORT") is None else int(os.getenv("PORT"))

UPLOAD_FOLDER = 'static/'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "./" + UPLOAD_FOLDER

tgtok = os.getenv("TELEGRAM_TOKEN")
assert tgtok is not None
tgbot = bot.Bot(tgtok)

def rand_str(l):
    return ''.join(random.choice(string.ascii_lowercase) for i in range(l))

def remove_old_imgs():
    now = time.time()
    for f in os.listdir(app.config['UPLOAD_FOLDER']):
        if os.stat(os.path.join(app.config['UPLOAD_FOLDER'], f)).st_mtime < now - 60*60:
            os.unlink(os.path.join(app.config['UPLOAD_FOLDER'], f))

@app.route('/uploader', methods = ['POST'])
def upload_file():
    board_id = request.args.get("id")
    if 'file' not in request.files:
        return "no file in request"
    file = request.files['file']
    if file.filename == '':
        return jsonify(error = "no selected file name")
    if file:
        remove_old_imgs()
        filename = secure_filename(file.filename)
        ext = os.path.splitext(filename)[1]
        filename = rand_str(16) + ext
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        is_new, idx, similarity = do_magic(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        img_fo = None
        if is_new is not None:
            img_fo = open(UPLOAD_FOLDER + filename, "rb")
        print (board_id, str(idx), similarity)
        tgbot.send_notification(board_id, str(idx), img_fo)
        if is_new is None:
            return "face not found"
        return "ok"
    return "invalid file"

@app.route('/image/<name>')
def get_image(name):
    path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(name))
    if os.path.splitext(name)[1] == ".png":
        return send_file(path, mimetype="image/png")
    if os.path.splitext(name)[1] == ".jpg":
        return send_file(path, mimetype="image/jpeg")
    return send_file(path)

INDEX_NAME = "./disk_index"
TRESHOLD = 0.3

def do_magic(filename):
    img = face_recognition.load_image_file(filename)
    encodings = face_recognition.face_encodings(img)
    if len(encodings) < 1:
        return None, None, None #face not found
    enc = np.array(encodings[0], dtype=np.float32)
    enc.shape = (1, 128)
    
    index = faiss.read_index(INDEX_NAME)
    D, I = index.search(enc, 1)
    similarity = D[0][0]
    idx = I[0][0]
    
    if similarity > TRESHOLD:
        # new face
        idx = index.ntotal
        index.add(enc)
        faiss.write_index(index, INDEX_NAME)
        return True, idx, similarity

    return False, idx, similarity


if not os.path.exists(INDEX_NAME):
    index = faiss.IndexFlatL2(128)
    faiss.write_index(index, INDEX_NAME)

if __name__ == "__main__":
    tgbot.start()
    app.run(host="0.0.0.0", port=PORT)
