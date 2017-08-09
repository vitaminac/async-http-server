# coding=utf-8
from response import Response


class Application:
    def __init__ (self):
        self.rules = { }

    def route (self, path):
        def wrapper (f):
            self.rules[path] = f
            return f

        return wrapper

    def __call__ (self, environ, start_response, *args, **kwargs):
        if self.rules[environ["PATH_INFO"]]:
            rv = self.rules[environ["PATH_INFO"]]()
            code = 200
        else:
            rv = "not found"
            code = 404
        return Response(code, rv)
