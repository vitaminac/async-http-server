# coding=utf-8
from config import Config
from flask import Flask, request, send_file

app = Flask(__name__)


@app.route('/')
def hello_world():
    return request.headers


@app.route("/static/file")
def file_provide_test():
    return send_file("./static/testFile.htm")


app.run(Config.host, Config.port, threaded=True)
