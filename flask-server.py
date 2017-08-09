# coding=utf-8
from flask import Flask
from config import Config

app = Flask(__name__)


@app.route('/')
def hello_world ():
    return Config.message


app.run(Config.host, Config.port)
