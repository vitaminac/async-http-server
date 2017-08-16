# coding=utf-8
class StreamSock:
    """Base class for transports."""

    def __init__(self, extra = None):
        if extra is None:
            extra = { }
        self._extra = extra
        assert loop is not None
        self._loop = loop
        self._protocol_paused = False
        self._set_write_buffer_limits()

    def get_extra_info(self, name, default = None):
        """Get optional transport information."""
        return self._extra.get(name, default)

    def is_closing(self):
        """Return True if the transport is closing or closed."""
        raise NotImplementedError

    def close(self):
        """Close the transport.

        Buffered data will be flushed asynchronously.  No more data
        will be received.  After all buffered data is flushed, the
        protocol's connection_lost() method will (eventually) called
        with None as its argument.
        """
        raise NotImplementedError

    def set_protocol(self, protocol):
        """Set a new protocol."""
        raise NotImplementedError

    def get_protocol(self):
        """Return the current protocol."""
        raise NotImplementedError
