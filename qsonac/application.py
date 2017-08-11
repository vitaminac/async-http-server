# coding=utf-8
from qsonac.request import Request
from qsonac.response import Response
from qsonac.urlmap import URLMap


class Application:
    def __init__ (self):
        self.rules = URLMap()

    def route (self, rule):
        def wrapper (f):
            self.add_routing(rule, f)
            return f

        return wrapper

    def __call__ (self, environ, start_response, *args, **kwargs):
        rq = self.make_request(environ)
        rv = self.dispatch_request(rq)
        if not isinstance(rv, tuple):
            rv = (200, rv)
        return self.make_response(*rv)

    def make_response (self, code, rv):
        return Response(code, rv)

    def add_routing (self, rule, handle):
        self.rules.add_rule(rule, handle)

    def dispatch_request (self, request):
        path = request.path
        handle = self.rules[path]
        if not handle:
            handle = self.not_found
        return handle(request=request)

    def not_found (self, *args, **kwargs):
        return 404, "not found"

    def make_request (self, environ):
        return Request(environ=environ)
