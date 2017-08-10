# coding=utf-8
from sockethttpserver import serve
from application import Application
from config import Config

app = Application()


@app.route("/")
def hello (*args, **kwargs):
    return kwargs["request"].headers["COOKIE"]


serve(app, host=Config.host, port=Config.port)
