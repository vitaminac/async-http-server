# coding=utf-8

import socket
import threading

from config import Config


class HttpHandle(threading.Thread):
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
            headers = dict([(s[0], "".join(s[1:])) for s in ([header.split(":") for header in html.split("\n")[1:]])])
            print(headers)
            for chunk in app({
                "PATH_INFO": "/"
            }, None):
                conn.sendall(chunk)
        finally:
            conn.shutdown(socket.SHUT_RDWR)
            conn.close()


def serve (app):
    # create and INET STREAMing socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((Config.host, Config.port))
    server_socket.listen(5)

    while True:
        (client_socket, address) = server_socket.accept()
        worker = HttpHandle(args=(client_socket, address, app))
        worker.start()
        # worker.daemon = True
        worker.join()
        print("current thread list : length:", len(threading.enumerate()), threading.enumerate())
