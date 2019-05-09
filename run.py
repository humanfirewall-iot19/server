from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from srv import app, tgbot
import os

tgbot.start()

http_server = HTTPServer(WSGIContainer(app))
http_server.listen(8080 if os.getenv("PORT") is None else int(os.getenv("PORT")), '0.0.0.0')
IOLoop.instance().start()
