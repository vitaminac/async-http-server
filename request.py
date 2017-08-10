# coding=utf-8
class Request:
    def __init__ (self, path: str = None, environ = None, *args, **kwargs):
        self.path = path
        self.headers = { }
        if environ:
            self.make_from_environ(environ)

    def make_from_environ (self, environ: dict):
        self.path = environ["PATH_INFO"]
        for key, value in environ.items():
            if key.startswith("HTTP_"):
                self.headers[key.replace("HTTP_", "")] = value
