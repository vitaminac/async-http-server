# coding=utf-8

import socket


def makeWSGIhandler (wsgi_app):
    class WSGIRequestHandler():
        app = wsgi_app

        def __init__ (self, request, client_address):
            self.request = request
            self.client_address = client_address
            self.handle()

        def handle (self):
            chunks = []
            chunk = self.request.recv(1024)
            handle_len = len(chunk)
            chunks.append(chunk)
            while not handle_len < 1024:
                chunk = self.request.recv(1024)
                handle_len = len(chunk)
                chunks.append(chunk)
            html = b''.join(chunks).decode("utf-8").strip()
            print(html)
            print()
            self.run_wsgi(self.request, wsgi_app, html)

        def run_wsgi (self, conn, app, rv):

            def write (msg):
                length = len(msg)
                totalsent = 0
                while totalsent < length:
                    sent = conn.send(msg[totalsent:])
                    if sent == 0:
                        raise RuntimeError("socket connection broken")
                    totalsent = totalsent + sent

            def start_response (status, response_headers, exc_info = None):
                return write

            def execute (app, request_text):
                environ = self.make_environ(request_text)
                for chunk in app(environ, start_response):
                    write(chunk)

            execute(app, rv)

        def make_environ (self, request_text):
            info = request_text.split("\n")
            environ = {
                "PATH_INFO": "/"
            }
            self.headers = dict([(s[0], "".join(s[1:])) for s in ([header.strip().split(":") for header in info[1:]])])
            for key, value in self.headers.items():
                key = key.upper().replace('-', '_')
                if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                    key = 'HTTP_' + key
                environ[key] = value
            return environ

    return WSGIRequestHandler
