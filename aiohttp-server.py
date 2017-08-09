# coding=utf-8
from aiohttp import web
from config import Config


async def hello (request):
    r = web.Response(text=Config.message)
    r.force_close()
    return r


app = web.Application()
app.router.add_get('/', hello)
web.run_app(app, host=Config.host, port=Config.port)
