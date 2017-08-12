# coding=utf-8
from flask import Flask, send_file
from config import Config

app = Flask(__name__)


@app.route('/')
def hello_world ():
    return Config.message


@app.route("/static/file")
def file_provide_test ():
    return send_file("testFile.htm")


app.run(Config.host, Config.port, threaded=True)
