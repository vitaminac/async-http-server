# coding=utf-8

import asyncio
import socket
import threading
from selectors import EVENT_READ, SelectSelector

from qsonac.handler import makeWSGIhandler


class AsyncHTTPServer:
    # make it in class level, so can be accessed from class method, handle_one_request
    RequestHandlerClass = None
    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    daemon_threads = True

    version = "socket server"

    def __init__(self, requestHandlerClass, loop, client_address = ("127.0.0.1", 80), request_queue_size = 5, multithread = True, multiprocess = False):
        self.loop = loop
        self.multithread = multithread
        self.multiprocess = multiprocess
        self.request_queue_size = request_queue_size
        self.__class__.RequestHandlerClass = requestHandlerClass
        self.host, self.port = client_address
        # create and INET STREAMing socket
        self.server_socket = socket.socket(self.address_family, self.socket_type)
        self.__shutdown_request = False

    def __enter__(self):
        self.server_bind()
        self.server_activate()
        return self

    def server_bind(self):
        self.server_socket.bind((self.host, self.port))

    def server_activate(self):
        # become a server socket
        # maximum number of queued connections
        self.server_socket.listen(self.request_queue_size)
        print("listening on ", "http://" + self.host + ":" + str(self.port))

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.server_socket.close()

    def serve_forever(self, poll_interval = 0.5):
        """ Main loop awaiting connections """
        with SelectSelector() as selector:
            selector.register(self, EVENT_READ)
            while not self.__shutdown_request:
                ready = selector.select(poll_interval)
                if ready:
                    try:
                        self.handle_request()
                    except Exception as e:
                        print(e)

                self.service_actions()

    def service_actions(self):
        pass

    def get_request(self):
        # conn - socket to client
        # addr - clients address
        client_socket, client_address = self.server_socket.accept()
        print("Got connection from:", client_address, client_socket)
        return client_socket, client_address

    def handle_request(self):
        # Handle one request
        try:
            request, client_address = self.get_request()
        except OSError:
            return
        worker = threading.Thread(target=self.__class__.handle_one_request, args=(request, client_address, self))
        worker.daemon = self.daemon_threads
        # worker.join()
        worker.start()

    @classmethod
    def handle_one_request(cls, request, client_address, server):
        cls.log(request, client_address)
        try:
            if cls.verify_request(request, client_address):
                cls.process_request(request, client_address, cls.RequestHandlerClass, server)
        except Exception as e:
            cls.handle_error(request, client_address, e)
        finally:
            cls.shutdown_request(request)

    @staticmethod
    def log(request, client_address):
        print(threading.current_thread(), " start handling ", request, " from ", client_address)
        print("thread list:", len(threading.enumerate()), threading.enumerate())

    @staticmethod
    def process_request(request, client_address, RequestHandlerClass, server):
        return RequestHandlerClass(request, client_address, server)

    @staticmethod
    def verify_request(request, client_address):
        return True

    @staticmethod
    def shutdown_request(request):
        """Called to shutdown and close an individual request."""
        try:
            # explicitly shutdown.  socket.close() merely releases
            # the socket and waits for GC to perform the actual close.
            request.shutdown(socket.SHUT_WR)
            print(threading.current_thread(), " shutdown ", request)
        except OSError:
            pass  # some platforms may raise ENOTCONN here
        print(request, " closing")
        request.close()

    @staticmethod
    def handle_error(request, client_address, e):
        print(e, "happened during processing ", request, " from ", client_address)
        import traceback
        traceback.print_exc()

    def fileno(self):
        return self.server_socket.fileno()


def serve(app, host = "127.0.0.1", port = 38764, loop = None):
    handler_class = makeWSGIhandler(app)
    if not loop:
        loop = asyncio.get_event_loop()
    with AsyncHTTPServer(handler_class, loop, (host, port)) as server:
        server.serve_forever()
