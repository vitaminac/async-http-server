# coding=utf-8

import socket
import threading


class WSGIRequestHandle(threading.Thread):
    def run (self):
        self.handle(*self._args, **self._kwargs)

    def handle (self, conn, address, app):
        print(threading.current_thread(), " start handling ", socket, " ", address, "app")
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
            environ = self.make_environ(html)
            for chunk in app(environ, None):
                conn.sendall(chunk)
        finally:
            conn.shutdown(socket.SHUT_RDWR)
            conn.close()

    def wsgi (self):

        pass

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
