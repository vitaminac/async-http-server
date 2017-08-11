# coding=utf-8

import socket
import threading


class WSGIRequestHandle(threading.Thread):
    def run (self):
        self.handle(*self._args, **self._kwargs)

    def handle (self, conn, address, app):
        print(threading.current_thread(), " start handling ", socket, " ", address, " to ", app)
        try:
            chunks = []
            chunk = conn.recv(1024)
            handle_len = len(chunk)
            chunks.append(chunk)
            while not handle_len < 1024:
                chunk = conn.recv(1024)
                handle_len = len(chunk)
                chunks.append(chunk)
            html = b''.join(chunks).decode("utf-8").strip()
            print(html)
            self.run_wsgi(conn, app, html)

        finally:
            conn.shutdown(socket.SHUT_RDWR)
            conn.close()

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
                conn.sendall(chunk)

        execute(app, rv)

    def make_environ (self, request_text):
        environ = {
            "PATH_INFO": "/"
        }
        self.headers = dict([(s[0], "".join(s[1:])) for s in ([header.split(":") for header in request_text.split("\n")[1:]])])
        for key, value in self.headers.items():
            key = key.upper().replace('-', '_')
            if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                key = 'HTTP_' + key
            environ[key] = value
        return environ
