# coding=utf-8

from qsonac.headers import Headers
from qsonac.utils import cached_property


class Request:
    """
        Very basic request object.  This does not implement advanced stuff like
        entity tag parsing or cache controls.  The request object is created with
        the WSGI environment as first argument.

        There are a couple of mixins available that add additional functionality
        to the request object, there is also a class called `Request` which
        subclasses `BaseRequest` and all the important mixins.

        Request objects are **read only**.  Any modification are not
        allowed in any place.  Unlike the lower level parsing functions the
        request object will use immutable objects everywhere possible.

        Per default the request object will assume all the text data is `utf-8` encoded.

        Per default the request object will be added to the WSGI
        environment as `werkzeug.request` to support the debugging system.
        If you don't want that, set `populate_request` to `False`.

        The environment is initialized as shallow object around the environ.  Every operation that would modify the
        environ in any way (such as consuming form data) raises an exception
        unless the `shallow` attribute is explicitly set to `False`.  This
        is useful for middlewares where you don't want to consume the form
        data by accident.  A shallow request is not populated to the WSGI
        environment.

        .. versionchanged:: 0.5
           read-only mode was enforced by using immutables classes for all
           data.
    """

    #: the charset for the request, defaults to utf-8
    charset = 'utf-8'

    #: the error handling procedure for errors, defaults to 'replace'
    encoding_errors = 'replace'

    #: the maximum content length.  This is forwarded to the form data
    #: parsing function (:func:`parse_form_data`).  When set and the
    #: :attr:`form` or :attr:`files` attribute is accessed and the
    #: parsing fails because more than the specified value is transmitted
    #: a :exc:`~werkzeug.exceptions.RequestEntityTooLarge` exception is raised.
    #:
    #: Have a look at :ref:`dealing-with-request-data` for more details.
    #:
    #: .. versionadded:: 0.5
    max_content_length = 0

    #: the maximum form field size.  This is forwarded to the form data
    #: parsing function (:func:`parse_form_data`).  When set and the
    #: :attr:`form` or :attr:`files` attribute is accessed and the
    #: data in memory for post data is longer than the specified value a
    #: :exc:`~werkzeug.exceptions.RequestEntityTooLarge` exception is raised.
    #:
    #: Have a look at :ref:`dealing-with-request-data` for more details.
    #:
    #: .. versionadded:: 0.5
    max_form_memory_size = None

    #: the class to use for `args` and `form`.  The default is an
    #: :class:`~werkzeug.datastructures.ImmutableMultiDict` which supports
    #: multiple values per key.  alternatively it makes sense to use an
    #: :class:`~werkzeug.datastructures.ImmutableOrderedMultiDict` which
    #: preserves order or a :class:`~werkzeug.datastructures.ImmutableDict`
    #: which is the fastest but only remembers the last key.  It is also
    #: possible to use mutable structures, but this is not recommended.
    #:
    #: .. versionadded:: 0.6
    parameter_storage_class = dict

    #: the type to be used for list values from the incoming WSGI environment.
    #: By default an :class:`~werkzeug.datastructures.ImmutableList` is used
    #: (for example for :attr:`access_list`).
    #:
    #: .. versionadded:: 0.6
    list_storage_class = list

    #: the type to be used for dict values from the incoming WSGI environment.
    #: By default an
    #: :class:`~werkzeug.datastructures.ImmutableTypeConversionDict` is used
    #: (for example for :attr:`cookies`).
    #:
    #: .. versionadded:: 0.6
    dict_storage_class = dict

    #: The form data parser that shoud be used.  Can be replaced to customize
    #: the form date parsing.
    form_data_parser_class = None

    #: Optionally a list of hosts that is trusted by this request.  By default
    #: all hosts are trusted which means that whatever the client sends the
    #: host is will be accepted.
    #:
    #: This is the recommended setup as a webserver should manually be set up
    #: to only route correct hosts to the application, and remove the
    #: `X-Forwarded-Host` header if it is not being used (see
    #: :func:`werkzeug.wsgi.get_host`).
    #:
    #: .. versionadded:: 0.9
    trusted_hosts = None

    #: Indicates whether the data descriptor should be allowed to read and
    #: buffer up the input stream.  By default it's enabled.
    #:
    #: .. versionadded:: 0.9
    disable_data_descriptor = False

    def __init__(self, environ = None, *args, **kwargs):
        self.environ = environ
        self.environ['werkzeug.request'] = self
        self.path = self.environ.get('PATH_INFO')

    # region <getter>
    @property
    def url_charset(self):
        """
        The charset that is assumed for URLs.  Defaults to the value
        of :attr:`charset`.

        .. versionadded:: 0.6
        """
        return self.charset

    @cached_property
    def headers(self):
        """
        The headers from the WSGI environ
        """
        return Headers(self.environ)

    @cached_property
    def stream(self):
        """
        If the incoming form data was not encoded with a known mimetype
        the data is stored unmodified in this stream for consumption.  Most
        of the time it is a better idea to use :attr:`data` which will give
        you that data as a string.  The stream only returns the data once.

        this stream is properly guarded that you can't accidentally read past the length of the input. Werkzeug will
        internally always refer to this stream to read data which makes it
        possible to wrap this object with a stream that does filtering.

        .. versionchanged:: 0.9
           This stream is now always available but might be consumed by the
           form parser later on.  Previously the stream was only set if no
           parsing happened.

        The stream returned is not the raw WSGI stream in most cases but one that is safe to read from
        without taking into account the content length.
        """
        stream = self.environ['wsgi.input']
        content_length = self.environ.get('CONTENT_LENGTH') or self.max_content_length
        return stream

    """"""
    # endregion
