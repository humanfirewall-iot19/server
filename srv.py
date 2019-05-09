from flask import Flask, request, redirect, url_for, jsonify
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

BASE_URL = "http://66e0d81f.ngrok.io/"
PORT = 5000

UPLOAD_FOLDER = 'static/'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "./" + UPLOAD_FOLDER

tgbot = bot.Bot()

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
        img_url = BASE_URL + UPLOAD_FOLDER + filename
        print (board_id, str(idx), similarity, img_url)
        tgbot.send_notification(board_id, str(idx), img_url)
        return "ok"
    return "invalid file"

INDEX_NAME = "./disk_index"
TRESHOLD = 0.3

def do_magic(filename):
    img = face_recognition.load_image_file(filename)
    encodings = face_recognition.face_encodings(img)
    if len(encodings) < 1:
        raise RuntimeError("Face not found!")
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

if __name__ == "__main__":
    if not os.path.exists(INDEX_NAME):
        index = faiss.IndexFlatL2(128)
        faiss.write_index(index, INDEX_NAME)
    
    tgbot.start()
    app.run(port=PORT)
