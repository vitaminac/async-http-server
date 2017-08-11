# coding=utf-8
from config import Config
from qsonac.application import Application
from qsonac.server import serve

app = Application()


@app.route("/")
def hello (*args, **kwargs):
    return kwargs["request"].path


serve(app, host=Config.host, port=Config.port)
