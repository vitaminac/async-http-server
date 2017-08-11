# coding=utf-8

import socket
import threading

from qsonac.handler import WSGIRequestHandle


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
            self._wait_for_connections()
        except Exception as e:
            print(e)
            raise

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

            worker = WSGIRequestHandle(args=(client_socket, address, self.app))
            worker.start()
            # worker.daemon = True
            # worker.join()
            print("current thread list : length:", len(threading.enumerate()), threading.enumerate())


def serve (app, host = "127.0.0.1", port = 38764):
    server = Server(app, host, port)
    server.run()
