# coding=utf-8
from aiohttp import web
from config import config


async def hello (request):
    r = web.Response(text="Hello, world")
    r.force_close()
    return r


app = web.Application()
app.router.add_get('/', hello)
web.run_app(app, host=config["host"], port=config["port"])
