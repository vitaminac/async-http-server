# coding=utf-8

import socket
import threading
from functools import partial
from threading import Thread

from qsonac.handler import makeWSGIhandler


class HTTPServer:
    # make it in class level, so can be accessed from class method, handle_one_request
    RequestHandlerClass = None

    def __init__ (self, RequestHandlerClass, client_address = ("127.0.0.1", 80), request_queue_size = 5):
        self.request_queue_size = request_queue_size
        self.__class__.RequestHandlerClass = RequestHandlerClass
        self.host, self.port = client_address
        # create and INET STREAMing socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __enter__ (self):
        self.server_socket.bind((self.host, self.port))
        # become a server socket
        # maximum number of queued connections
        self.server_socket.listen(self.request_queue_size)
        return self

    def __exit__ (self, exc_type, exc_val, exc_tb):
        self.server_socket.close()

    def serve_forever (self):
        """ Main loop awaiting connections """
        while True:
            try:
                self.handle_request()
            except Exception as e:
                print(e)

    def get_request (self):
        print("Awaiting New connection")
        # conn - socket to client
        # addr - clients address
        client_socket, address = self.server_socket.accept()
        return client_socket, address

    def handle_request (self):
        # Handle one request
        try:
            request, client_address = self.get_request()
        except OSError:
            return

        worker = threading.Thread(target=self.handle_one_request, args=(request, client_address))
        # worker.daemon = True
        # worker.join()
        worker.start()
        print("current thread list : length:", len(threading.enumerate()), threading.enumerate())

    @classmethod
    def handle_one_request (cls, request, client_address):
        print(threading.current_thread(), " start handling ", request, " ", client_address)
        if cls.verify_request(request, client_address):
            try:
                cls.process_request(request, client_address, cls.RequestHandlerClass)
            except Exception as e:
                cls.handle_error(request, client_address, e)
                cls.shutdown_request(request)
            except:
                cls.shutdown_request(request)
                raise
        else:
            cls.shutdown_request(request)

    @staticmethod
    def process_request (request, client_address, RequestHandlerClass):
        RequestHandlerClass(request, client_address)

    @staticmethod
    def verify_request (request, client_address):
        print("Got connection from:", client_address)
        return True

    @staticmethod
    def shutdown_request (request):
        """Called to shutdown and close an individual request."""
        try:
            # explicitly shutdown.  socket.close() merely releases
            # the socket and waits for GC to perform the actual close.
            request.shutdown(socket.SHUT_WR)
        except OSError:
            pass  # some platforms may raise ENOTCONN here
        request.close()

    @staticmethod
    def handle_error (request, client_address, exception):
        print(exception, " happened during processing the connection from ", client_address)
        import traceback
        traceback.print_exc()

    def fileno (self):
        return self.server_socket.fileno()


def serve (app, host = "127.0.0.1", port = 38764):
    handler_class = makeWSGIhandler(app)
    with HTTPServer(handler_class, (host, port)) as server:
        server.serve_forever()
