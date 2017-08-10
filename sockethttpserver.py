# coding=utf-8

import socket
import threading


class RequestHandle(threading.Thread):
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


class Server:
    def __init__ (self, app, host = "127.0.0.1", port = 80):
        self.app = app
        self.host = host
        self.port = port

    def run (self):
        # create and INET STREAMing socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.server_socket.bind((self.host, self.port))
        except Exception as e:
            print(e)
        self._wait_for_connections()

    def _wait_for_connections (self):
        """ Main loop awaiting connections """
        # become a server socket
        self.server_socket.listen(5)  # maximum number of queued connections
        while True:
            print("Awaiting New connection")
            # conn - socket to client
            # addr - clients address
            client_socket, address = self.server_socket.accept()

            print("Got connection from:", address)

            worker = RequestHandle(args=(client_socket, address, self.app))
            worker.start()
            # worker.daemon = True
            worker.join()
            print("current thread list : length:", len(threading.enumerate()), threading.enumerate())


def serve (app, host = "127.0.0.1", port = 38764):
    server = Server(app, host, port)
    server.run()
