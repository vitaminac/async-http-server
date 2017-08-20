# coding=utf-8

import asyncio
import errno
import logging
import socket

from qsonac.handler import makeWSGIhandler
from qsonac.streamsock import StreamSock


class AsyncHTTPServer:
    # make it in class level, so can be accessed from class method, handle_one_request
    RequestHandlerClass = None
    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    daemon_threads = True

    version = "socket server"

    # Seconds to wait before retrying accept().
    ACCEPT_RETRY_DELAY = 1

    def __init__(self, requestHandlerClass, client_address = ("127.0.0.1", 80), loop = None, request_queue_size = 15, multithread = False, multiprocess = False):
        if not loop:
            loop = asyncio.get_event_loop()
        self.handler_list = { }
        self.loop = loop
        self.loop.set_debug(True)
        logging.getLogger('asyncio').setLevel(logging.WARNING)
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

    def start_serve(self):
        """ Main loop awaiting connections """
        # self._selector.register(self, selectors.EVENT_READ)
        # add event listener to server socket
        self.loop.add_reader(self, self.handle_requests)

    def serve_forever(self):
        self.start_serve()
        self.loop.run_forever()

    def handle_requests(self):
        # This method is only called once for each event loop tick where the
        # listening socket has triggered an EVENT_READ. There may be multiple
        # connections waiting for an .accept() so it is called in a loop.
        # See https://bugs.python.org/issue27906 for more details.
        for i in range(self.request_queue_size):
            try:
                # Handle one request
                request, client_address = self.accept_request()
            except (BlockingIOError, InterruptedError, ConnectionAbortedError):
                # Early exit because the socket accept buffer is empty.
                break
            except OSError as exc:
                # There's nowhere to send the error, so just log it.
                if exc.errno in (errno.EMFILE, errno.ENFILE,
                                 errno.ENOBUFS, errno.ENOMEM):
                    # Some platforms (e.g. Linux keep reporting the FD as
                    # ready, so we remove the read handler temporarily.
                    # We'll try again in a while.
                    self.log(self.server_socket, (self.host, self.port), str({
                        'message'  : 'socket.accept() out of system resource',
                        'exception': exc,
                        'socket'   : self.server_socket,
                    }))
                    self.loop.remove_reader(self)
                    self.loop.call_later(self.ACCEPT_RETRY_DELAY, self.start_serve)
                else:
                    raise  # The event loop will catch, log and ignore it.
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
        self.loop.create_task(self.handle_one_request(request, client_address, self))

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
        async with StreamSock(server.loop, request, server) as streamRW:
            async with RequestHandlerClass(streamRW) as handle:
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

    def attach(self, handler, conn):
        self.handler_list[handler] = conn

    def detach(self, handler, exc):
        del self.handler_list[handler]
        print(handler, exc)


def serve(app, host = "127.0.0.1", port = 38764, loop = None):
    handler_class = makeWSGIhandler(app)
    # asyncio.start_server(print)  # stupid
    with AsyncHTTPServer(handler_class, (host, port), loop) as server:
        server.serve_forever()
