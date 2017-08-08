# coding=utf-8

import socket
import threading

from config import config
from response import Response


class HttpHandle(threading.Thread):
    def run (self):
        self.handle(*self._args, **self._kwargs)

    def handle (self, conn, address):
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
            conn.send(str(Response("hello world")).encode("utf-8"))
        finally:
            conn.shutdown(socket.SHUT_RDWR)
            conn.close()


def start_server ():
    # create and INET STREAMing socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((config.host, config.port))
    server_socket.listen(5)

    while True:
        (client_socket, address) = server_socket.accept()
        worker = HttpHandle(args=(client_socket, address))
        worker.start()
        # worker.daemon = True
        worker.join()
        print("current thread list : length:", len(threading.enumerate()), threading.enumerate())

# start_server()
