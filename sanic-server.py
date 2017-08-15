# coding=utf-8
from sanic import Sanic
from sanic.response import json
from config import Config

app = Sanic()


@app.route("/")
async def test(request):
    return json({ "hello": "world" })


if __name__ == "__main__":
    app.run(host=Config.host, port=Config.port)
