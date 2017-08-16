# coding=utf-8

import socket

import asyncio
from qsonac.handler import makeWSGIhandler


class AsyncHTTPServer:
    # make it in class level, so can be accessed from class method, handle_one_request
    RequestHandlerClass = None
    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    daemon_threads = True

    version = "socket server"

    def __init__(self, requestHandlerClass, client_address = ("127.0.0.1", 80), loop = None, request_queue_size = 15, multithread = False, multiprocess = False):
        if not loop:
            loop = asyncio.get_event_loop()
        self.loop = loop
        self.multithread = multithread
        self.multiprocess = multiprocess
        self.request_queue_size = request_queue_size
        self.__class__.RequestHandlerClass = requestHandlerClass
        self.host, self.port = client_address

    def server_bind(self):
        self.server_socket.bind((self.host, self.port))

    def server_activate(self):
        # become a server socket
        # maximum number of queued connections
        self.server_socket.listen(self.request_queue_size)
        print(f"listening on http://{self.host}:{self.port}")

    def setup(self):
        # create and INET STREAMing socket
        self.server_socket = socket.socket(self.address_family, self.socket_type)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        if hasattr(socket, "SO_REUSEPORT"):
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, True)
        self.server_socket.setblocking(False)
        # self._selector = selectors.DefaultSelector()

    def __enter__(self):
        self.setup()
        self.server_bind()
        self.server_activate()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # self._selector.unregister(self)
        # self._selector.close()
        self.server_socket.close()

    def serve_forever(self):
        """ Main loop awaiting connections """
        # self._selector.register(self, selectors.EVENT_READ)
        # add event listener to server socket
        self.loop.add_reader(self, self.handle_requests)
        self.loop.run_forever()

    def handle_requests(self):
        # the call won’t block, and will report the currently ready file objects
        # ready = self._selector.select(0)
        # print(self.server_socket, "become ready")
        # while ready:
        #     self.deal_one_request()
        #     ready = self._selector.select(0)
        for i in range(self.request_queue_size):
            try:
                # Handle one request
                request, client_address = self.accept_request()
            except (BlockingIOError, InterruptedError, ConnectionAbortedError):
                # Early exit because the socket accept buffer is empty.
                break
            else:
                self.create_new_request_handler(request, client_address)
        # perform periodic task
        self.service_actions()

    def service_actions(self):
        # print("thread list:", len(threading.enumerate()), threading.enumerate())
        print(asyncio.Task.all_tasks())

    def accept_request(self):
        # conn - socket to client
        # addr - clients address
        client_socket, client_address = self.server_socket.accept()
        self.log(client_socket, client_address, "Got")
        return client_socket, client_address

    def create_new_request_handler(self, request, client_address):
        # worker = threading.Thread(target=self.__class__.process_request, args=(request, client_address, self))
        # worker.daemon = self.daemon_threads
        # # worker.join()
        # worker.start()
        asyncio.ensure_future(self.handle_one_request(request, client_address, self), loop=self.loop)

    @classmethod
    @asyncio.coroutine
    def handle_one_request(cls, request, client_address, server):
        cls.log(request, client_address, "start handling")
        try:
            if cls.verify_request(request, client_address):
                yield from cls.process_request(request, client_address, cls.RequestHandlerClass, server)
                cls.finish_request(request, client_address)
        except Exception as e:
            cls.handle_error(request, client_address, e)
        finally:
            cls.shutdown_request(request)

    @staticmethod
    def log(request, client_address: tuple = "", msg: str = "", *args):
        # print(threading.current_thread(), " start handling ", request, " from ", client_address)
        print(asyncio.Task.current_task(), msg, request, " from ", client_address)

    @staticmethod
    async def process_request(request, client_address, RequestHandlerClass, server):
        async with RequestHandlerClass(request, client_address, server) as handle:
            return await handle

    @staticmethod
    def verify_request(request, client_address):
        return True

    @staticmethod
    def finish_request(request, client_address):
        # a hook function for future use
        pass

    @classmethod
    def shutdown_request(cls, request):
        """Called to shutdown and close an individual request."""
        try:
            # explicitly shutdown.  socket.close() merely releases
            # the socket and waits for GC to perform the actual close.
            request.shutdown(socket.SHUT_WR)
            cls.log(request, msg="shutdown")
        except OSError:
            pass  # some platforms may raise ENOTCONN here
        request.close()
        cls.log(request, msg="hsa closed")

    @classmethod
    def handle_error(cls, request, client_address, e):
        cls.log(request, client_address, "exception raised during processing", e)
        import traceback
        traceback.print_exc()

    def fileno(self):
        return self.server_socket.fileno()


def serve(app, host = "127.0.0.1", port = 38764, loop = None):
    handler_class = makeWSGIhandler(app)
    # asyncio.start_server(print)  # stupid
    with AsyncHTTPServer(handler_class, (host, port), loop) as server:
        server.serve_forever()
