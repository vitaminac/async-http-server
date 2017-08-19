# coding=utf-8
import socket

import asyncio


class StreamSock:
    """
        State machine of calls:

          start -> DR* -> ER? -> SD -> CS -> end

        * DR: data_received()
        * ER: eof_received()
        * SD: shutdown()
        * CS: close()
    """
    buffer_factory = bytearray  # Constructs initial value for self._buffer.

    def __init__(self, loop: asyncio.SelectorEventLoop, sock: socket.socket, server = None):
        self._loop = loop
        self.exception = None
        self._waiter = None  # A future used by wait_for_()

        """SocketTransport"""
        self._sock = sock
        self._buffer_limit = 2 ** 16

        """StreamProtocol"""
        self._server = server

        """StreamWriter"""
        self._write_buffer = self.buffer_factory()
        self._write_pause = False
        self._write_eof = False  # next drain will transmit all data in write_buffer

        """StreamReader"""
        self._read_buffer = self.buffer_factory()
        self._read_paused = False
        self._read_eof = False  # when all data are in read_buffer

    # region <getter>

    @property
    def socket(self):
        return self._sock

    @property
    def server(self):
        return self._server

    @property
    def server_address(self):
        return self.socket.getsockname()

    @property
    def host(self):
        return self.server_address[0]

    @property
    def port(self):
        return self.server_address[1]

    @property
    def remote_address(self):
        return self.socket.getpeername()

    @property
    def remote_host(self):
        return self.remote_address[0]

    @property
    def remote_port(self):
        return self.remote_address()[1]

    def fileno(self):
        return self.socket.fileno()

    # endregion

    # region <static method>

    @staticmethod
    def configure_connection(socket):
        socket.setblocking(False)
        # Disable the Nagle algorithm -- small writes will be
        # sent without waiting for the TCP ACK.  This generally
        # decreases the latency (in some cases significantly.)
        if hasattr(socket, 'TCP_NODELAY'):
            socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)

    # endregion

    # region <asynchronous action control flow>
    def setup(self):
        self.configure_connection(self.socket)
        self.set_write_buffer_limits()
        self.pause_read()  # fill read buffer

    async def __aenter__(self):
        self.setup()
        if self.server is not None:
            self.server.attach(self, self.socket)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        if self.server is not None:
            self.server.detach(self, self, self.exception)
            self._server = None

    async def __aiter__(self):
        return self

    async def __anext__(self):
        val = await self.readline()
        if val == b'':
            raise StopAsyncIteration
        return val

    async def wait_stream_ready(self):
        waiter = self._waiter
        assert waiter is None or waiter.cancelled() or waiter.done()
        waiter = self._loop.create_future()
        self._waiter = waiter
        return await waiter

    def _wakeup_waiter(self):
        """Wakeup  functions waiting for reading/writing data or EOF."""
        waiter = self._waiter
        if waiter is not None:
            self._waiter = None
            assert not waiter.cancelled() and not waiter.done()
            waiter.set_result(self.exception)  # if had exception set to waiter

    # endregion

    # region <close method>

    def release_resource(self):
        self._read_buffer.clear()
        self._write_buffer.clear()
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
        self._sock = None
        self._loop = None

    def _force_close(self):
        self._loop.remove_reader(self)
        self._loop.remove_writer(self)
        self.closed = True
        self.release_resource()

    def abort(self):
        """Close the transport immediately.

        Buffered data will be lost.  No more data will be received.
        The protocol's connection_lost() method will (eventually) be
        called with None as its argument.
        """
        self._force_close()

    async def close(self):
        """
        Close the transport.

        Buffered data will be flushed asynchronously.  No more data
        will be received.  After all buffered data is flushed, the
        protocol's connection_lost() method will (eventually) called
        with None as its argument.
        """
        self.feed_eof()
        # try to drain all data in timeout interval
        self.write_eof()
        try:
            await asyncio.wait_for(self.drain(), 5)  # wait at most 5 sec, and force close it
        except Exception as e:
            self.exception = e
        self._force_close()

    def _fatal_error(self, exc, message = 'Fatal error on transport'):
        # Should be called from exception handler only.
        self.exception = exc
        self._wakeup_waiter()  # wake up with exception
        self.abort()

    # endregion

    # region <stream flow control>

    # region <EOF>

    def feed_eof(self):
        """
            Called when the peer close the conversation or connection broken.

            If this returns a false value (including None), the transport
            will close itself.  If it returns a true value, closing the
            transport is up to the protocol.
        """
        self._read_eof = True
        # We're keeping the connection open so the
        # protocol can write more, but we still can't
        # receive more, so remove the reader callback.
        self._loop.remove_reader(self)
        self.socket.shutdown(socket.SHUT_RD)
        return True

    def write_eof(self):
        """Close the write end after flushing buffered data.

        (This is like typing ^D into a UNIX program reading from stdin.)

        Data may still be received.
        """
        self._write_eof = True
        # shutdown will be done in next drain
        # ensure next drain will send all data in write buffer
        self.set_write_buffer_limits(0)
        # schedule the drain
        self._loop.create_task(self.drain())

    # endregion

    # pause stream when buffer full(writing), empty(reading) , and wait until underlying resource prepared for write/read again

    # region <read-only>

    def pause_read(self):
        """
        Pause all read method, wait to receive underlying data into read_buffer
        """
        assert self._read_paused, 'Already paused'
        self._read_paused = True
        self._loop.add_reader(self, self.feed_data_when_ready)
        print("%r pauses reading", self)

    def resume_read(self):
        """
        read buffer filled, now can be read again, wake up any coroutine function that wait for read
        """
        assert not self._read_paused, 'Not paused'
        self._read_paused = False
        self._loop.remove_reader(self)
        self._wakeup_waiter()
        print("%r resumes reading", self)

    def feed_data_when_ready(self):
        """
            Called when some data is received.
            The argument is a bytes object.
        """
        assert not self._read_eof, "try to receive after feed EOF"
        try:
            data = self._sock.recv(self._buffer_limit * 4)  # Buffer size passed to recv().
        except (BlockingIOError, InterruptedError):
            pass
        except Exception as e:
            self._fatal_error(e)
        else:
            if data:
                self._read_buffer.extend(data)
            else:
                print("%r received EOF", self)
                self.feed_eof()
            self.resume_read()

    async def wait_for_data(self, force = False):
        """
        Wait until feed_data() or feed_eof() is called.

        If stream was paused, automatically resume it.
        """
        # StreamReader uses a future to link the protocol feed_data() method
        # to a read coroutine. Running two read coroutines at the same time
        # would have an unexpected behaviour. It would not possible to know
        # which coroutine would get the next data.

        assert not self._read_eof, '_wait_for_data after EOF'
        if len(self._read_buffer) <= self._buffer_limit or force:
            # Waiting for data while paused will make deadlock, so prevent it.
            # This is essential for readexactly(n) for case when n > self._limit.
            self.pause_read()
            await self.wait_stream_ready()

    # endregion

    # region <write-only>

    def pause_write(self):
        """
        Called when the transport's buffer goes over the high-water mark.

        Pause and resume calls are paired -- pause_writing() is called
        once when the buffer goes strictly over the high-water mark
        (even if subsequent writes increases the buffer size even
        more), and eventually resume_writing() is called once when the
        buffer size reaches the low-water mark.

        Note that if the buffer size equals the high-water mark,
        pause_writing() is not called -- it must go strictly over.
        Conversely, resume_writing() is called when the buffer size is
        equal or lower than the low-water mark.  These end conditions
        are important to ensure that things go as expected when either
        mark is zero.

        NOTE: This is the only Protocol callback that is not called
        through EventLoop.call_soon() -- if it were, it would have no
        effect when it's most needed (when the app keeps writing
        without yielding until pause_writing() is called).
        """
        assert not self._write_pause
        self._write_pause = True
        self._loop.add_writer(self, self.write_data_when_ready)
        print("%r pauses writing", self)

    def resume_write(self):
        """Called when the transport's buffer drains below the low-water mark.

        See pause_writing() for details.
        """

        assert self._write_pause
        self._write_pause = False
        self._loop.remove_writer(self)
        print("%r resumes writing", self)
        self._wakeup_waiter()

    def write_data_when_ready(self):
        assert self._write_buffer, 'Data should not be empty'

        try:
            n = self._sock.send(self._write_buffer)
        except (BlockingIOError, InterruptedError):
            pass
        except Exception as e:
            self._fatal_error(e)
        else:
            if n:
                del self._write_buffer[:n]
            if self.get_write_buffer_size() <= self._low_water:  # now can write more
                self.resume_write()  # wake up the waiter, usually is self.drain
                if self._write_eof and not self._write_buffer:
                    self._sock.shutdown(socket.SHUT_WR)

    async def drain(self):
        """
            Flush the write buffer.

            The intended use is to write

            w.write(data)
            yield from w.drain()
        """
        # drain until lower than low water when current write buffer exceed high water
        # if EOF was written wait to drain all
        while self.get_write_buffer_size() > self._high_water:
            self.pause_write()
            await self.wait_stream_ready()

    # endregion

    # endregion

    # region <stream info>

    def get_write_buffer_limits(self):
        return (self._low_water, self._high_water)

    def set_write_buffer_limits(self, high = None, low = None):
        """Set the high- and low-water limits for write flow control.

        These two values control when to call the protocol's
        pause_writing() and resume_writing() methods.  If specified,
        the low-water limit must be less than or equal to the
        high-water limit.  Neither value can be negative.

        The defaults are implementation-specific.  If only the
        high-water limit is given, the low-water limit defaults to an
        implementation-specific value less than or equal to the
        high-water limit.  Setting high to zero forces low to zero as
        well, and causes pause_writing() to be called whenever the
        buffer becomes non-empty.  Setting low to zero causes
        resume_writing() to be called only once the buffer is empty.
        Use of zero for either limit is generally sub-optimal as it
        reduces opportunities for doing I/O and computation
        concurrently.
        """
        if high is None:
            if low is None:
                high = self._buffer_limit
            else:
                high = 4 * low
        if low is None:
            low = high // 4
        self._high_water = high
        self._low_water = low

    def get_write_buffer_size(self):
        """Return the current size of the write buffer."""
        return len(self._write_buffer)

    def at_eof(self):
        """Return True if the buffer is empty and 'feed_eof' was called."""
        return self._read_eof and not self._read_buffer

    # endregion

    # region <StreamReader>

    async def readline(self, limit = None):
        """
        Limit sets the maximal length of data that can be returned, not counting the newline.

        Read chunk of data from the stream until newline (b'\n') is found or reach the limit or EOF.

        On success, complete line including newline will be returned and will be removed
        from internal buffer. if reach EOF or limit return current read bytes (whole read_buffer or limit bytes)
        """
        separator = b'\n'
        seplen = len(separator)
        if not limit:
            limit = self._buffer_limit

        """
            `offset` is the number of bytes from the beginning of the buffer
            where there is no occurrence of `separator`.
        """
        block = await self.read(limit)
        isep = block.find(block) # isep wont be larger than limit
        # `newline` not in the buffer. `isep` will be used later to retrieve the data.
        if isep < 0 or self._read_eof:
            isep = len(block) - 1

        chunk = block[:isep + seplen]
        self._read_buffer = block[isep + seplen:] + self._read_buffer
        return bytes(chunk)

    async def read(self, n = -1):
        """
        Read up to `n` bytes from the stream.
        If n is not provided, or set to -1, read until EOF and return all read bytes.
        If n is zero, return empty bytes object immediately.
        If n is positive, this function try to read `n` bytes, and may return
        less or equal bytes than requested, but at least one byte. If the EOF was received before reach n bytes, then return until EOF
        If stream was paused, this function will automatically resume it if needed.
        """

        if n == 0:
            return b''

        if n < 0:
            # wait to receive EOF
            blocks = []
            while not self._read_eof:
                await self.wait_for_data(True)

        while len(self._read_buffer) < n and not self._read_eof:
            await self.wait_for_data(True)

        # This will work right even if buffer is less than n bytes
        data = bytes(self._read_buffer[:n])
        del self._read_buffer[:n]
        await self.wait_for_data()  # fetch data if need
        return data

    # endregion

    # region <StreamWriter>
    """
        This exposes write(), writelines().  It adds drain() which returns an
        optional Future on which you can wait for flow control.  It also
        adds a transport property which references the Transport
        directly.
    """

    async def write(self, data):
        """
        Write some data bytes to the transport.

        This does not block; it buffers the data and arranges for it
        to be sent out asynchronously.
        """
        if self._write_eof:
            raise RuntimeError('Cannot call write() after write_eof()')
        if not data:
            return

        self._write_buffer.extend(data)  # Add it to the buffer.
        return await self.drain()  # drain data if need

    async def writelines(self, list_of_data):
        """
        Write a list (or any iterable) of data bytes to the transport.

        The default implementation concatenates the arguments and
        calls write() on the result.
        """
        data = b''.join(bytes(data) if isinstance(data, memoryview) else data for data in list_of_data)
        return await self.write(data)

    # endregion

    ""
