# coding=utf-8
from config import Config
from qsonac.application import Application
from qsonac.asynchttpserver import serve

app = Application()


@app.route("/")
def hello(*args, **kwargs):
    request = kwargs.pop("request")
    return str(request.headers)


@app.route("/static/file")
def file_provide_test(*args, **kwargs):
    return app.send_static_file("./static/testFile.htm")


serve(app, host=Config.host, port=Config.port)
