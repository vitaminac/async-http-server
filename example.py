# coding=utf-8
from server import serve
from application import Application

app = Application()


@app.route("/")
def hello ():
    return "hello"


serve(app)
