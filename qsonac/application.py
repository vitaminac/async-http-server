# coding=utf-8
from qsonac.request import Request
from qsonac.response import Response
from qsonac.urlmap import URLMap


class Application:
    Request_class = Request
    Response_class = Response

    def __init__(self):
        self.rules = URLMap()

    def route(self, rule):
        def wrapper(f):
            self.add_routing(rule, f)
            return f

        return wrapper

    def __call__(self, environ: dict, start_response):
        """
        PEP 3333, copied from https://www.python.org/dev/peps/pep-3333/#specification-details

        The application object must accept two positional arguments.
        For the sake of illustration, we have named them environ and start_response,
        but they are not required to have these names. A server or gateway must invoke the application object using positional (not keyword) arguments.
        (E.g. by calling result = application(environ, start_response) as shown above.)

        The environ parameter is a dictionary object, containing CGI-style environment variables.
        This object must be a builtin Python dictionary (not a subclass,
        UserDict or other dictionary emulation),
        and the application is allowed to modify the dictionary in any way it desires.
        The dictionary must also include certain WSGI-required variables (described in a later section),
        and may also include server-specific extension variables,
        named according to a convention that will be described below.

        The start_response parameter is a callable accepting two required positional arguments,
        and one optional argument. For the sake of illustration,
        we have named these arguments status, response_headers, and exc_info,
        but they are not required to have these names,
        and the application must invoke the start_response callable using positional arguments
        (e.g. start_response(status, response_headers)).

        The status parameter is a status string of the form "999 Message here",
        and response_headers is a list of (header_name, header_value) tuples describing the HTTP response header.
        The optional exc_info parameter is described below in the sections on The start_response() Callable and Error Handling.
        It is used only when the application has trapped an error and is attempting to display an error message to the browser.

        The start_response callable must return a write(body_data) callable that takes
        one positional parameter: a bytestring to be written as part of the HTTP response body.
        (Note: the write() callable is provided only to support certain existing frameworks' imperative output APIs;
        it should not be used by new applications or frameworks if it can be avoided.
        See the Buffering and Streaming section for more details.)

        When called by the server, the application object must return an iterable yielding zero or more bytestrings.
        This can be accomplished in a variety of ways, such as by returning a list of bytestrings,
        or by the application being a generator function that yields bytestrings,
        or by the application being a class whose instances are iterable.
        Regardless of how it is accomplished, t
        he application object must always return an iterable yielding zero or more bytestrings.

        The server or gateway must transmit the yielded bytestrings to the client in an unbuffered fashion,
        completing the transmission of each bytestring before requesting another one.
        (In other words, applications should perform their own buffering.
        See the Buffering and Streaming section below for more on how application output must be handled.)

        The server or gateway should treat the yielded bytestrings as binary byte sequences:
        in particular, it should ensure that line endings are not altered.
        The application is responsible for ensuring that the bytestring(s) to be written are in a format suitable for the client.
        (The server or gateway may apply HTTP transfer encodings,
        or perform other transformations for the purpose of implementing HTTP features such as byte-range transmission.
        See Other HTTP Features, below, for more details.)

        If a call to len(iterable) succeeds, the server must be able to rely on the result being accurate.
        That is, if the iterable returned by the application provides a working __len__() method,
        it must return an accurate result.
        (See the Handling the Content-Length Header section for information on how this would normally be used.)

        If the iterable returned by the application has a close() method,
        the server or gateway must call that method upon completion of the current request,
        whether the request was completed normally,
        or terminated early due to an application error during iteration or an early disconnect of the browser.
        (The close() method requirement is to support resource release by the application.
        This protocol is intended to complement PEP 342's generator support,
        and other common iterables with close() methods.)

        Applications returning a generator or other custom iterator should not assume the entire iterator will be consumed,
        as it may be closed early by the server.

        (Note: the application must invoke the start_response() callable before the iterable yields its first body bytestring,
        so that the server can send the headers before any body content.
        However, this invocation may be performed by the iterable's first iteration,
        so servers must not assume that start_response() has been called before they begin iterating over the iterable.)

        Finally, servers and gateways must not directly use any other attributes of the iterable returned by the application,
        unless it is an instance of a type specific to that server or gateway,
        such as a "file wrapper" returned by wsgi.file_wrapper (see Optional Platform-Specific File Handling).
        In the general case, only attributes specified here, or accessed via e.g. the PEP 234 iteration APIs are acceptable.

        environ Variables
        The environ dictionary is required to contain these CGI environment variables,
        as defined by the Common Gateway Interface specification [2].
        The following variables must be present, unless their value would be an empty string,
        in which case they may be omitted, except as otherwise noted below.

        REQUEST_METHOD
            The HTTP request method, such as "GET" or "POST". This cannot ever be an empty string, and so is always required.
        SCRIPT_NAME
            The initial portion of the request URL's "path" that corresponds to the application object,
            so that the application knows its virtual "location". This may be an empty string,
            if the application corresponds to the "root" of the server.
        PATH_INFO
            The remainder of the request URL's "path", designating the virtual "location" of the request's target within the application.
            This may be an empty string, if the request URL targets the application root and does not have a trailing slash.
        QUERY_STRING
            The portion of the request URL that follows the "?", if any. May be empty or absent.
        CONTENT_TYPE
            The contents of any Content-Type fields in the HTTP request. May be empty or absent.
        CONTENT_LENGTH
            The contents of any Content-Length fields in the HTTP request. May be empty or absent.
        SERVER_NAME, SERVER_PORT
            When combined with SCRIPT_NAME and PATH_INFO, these two strings can be used to complete the URL. Note,
            however, that HTTP_HOST, if present, should be used in preference to SERVER_NAME for reconstructing the request URL.
            See the URL Reconstruction section below for more detail.
            SERVER_NAME and SERVER_PORT can never be empty strings, and so are always required.
        SERVER_PROTOCOL
            The version of the protocol the client used to send the request.
            Typically this will be something like "HTTP/1.0" or "HTTP/1.1" and may be used by the application to determine how to treat any HTTP request headers.
            (This variable should probably be called REQUEST_PROTOCOL, since it denotes the protocol used in the request,
            and is not necessarily the protocol that will be used in the server's response. However,
            for compatibility with CGI we have to keep the existing name.)
        HTTP_ Variables
            Variables corresponding to the client-supplied HTTP request headers
            (i.e., variables whose names begin with "HTTP_").
            The presence or absence of these variables should correspond with the presence or absence of the appropriate HTTP header in the request.

        A server or gateway should attempt to provide as many other CGI variables as are applicable. In addition,
        if SSL is in use, the server or gateway should also provide as many of the Apache SSL environment variables [5] as are applicable,
        such as HTTPS=on and SSL_PROTOCOL.
        Note, however, that an application that uses any CGI variables other than the ones listed above are necessarily non-portable
        to web servers that do not support the relevant extensions.
        (For example, web servers that do not publish files will not be able to provide a meaningful DOCUMENT_ROOT or PATH_TRANSLATED.)

        A WSGI-compliant server or gateway should document what variables it provides, along with their definitions as appropriate.
        Applications should check for the presence of any variables they require,
        and have a fallback plan in the event such a variable is absent.

        Note: missing variables (such as REMOTE_USER when no authentication has occurred) should be left out of the environ dictionary.
        Also note that CGI-defined variables must be native strings, if they are present at all.
        It is a violation of this specification for any CGI variable's value to be of any type other than str.

        In addition to the CGI-defined variables, the environ dictionary may also contain arbitrary operating-system "environment variables",
        and must contain the following WSGI-defined variables:

        wsgi.version
            The tuple (1, 0), representing WSGI version 1.0.
        wsgi.url_scheme
            A string representing the "scheme" portion of the URL at which the application is being invoked.
            Normally, this will have the value "http" or "https", as appropriate.
        wsgi.input
            An input stream (file-like object) from which the HTTP request body bytes can be read.
            (The server or gateway may perform reads on-demand as requested by the application,
            or it may pre- read the client's request body and buffer it in-memory or on disk,
            or use any other technique for providing such an input stream, according to its preference.)
        wsgi.errors
            An output stream (file-like object) to which error output can be written,
            for the purpose of recording program or other errors in a standardized and possibly centralized location.
            This should be a "text mode" stream;
            i.e., applications should use "\n" as a line ending, and assume that it will be converted to the correct line ending by the server/gateway.

            (On platforms where the str type is unicode, the error stream should accept and log arbitrary unicode without raising an error;
            it is allowed, however, to substitute characters that cannot be rendered in the stream's encoding.)

            For many servers, wsgi.errors will be the server's main error log. Alternatively, this may be sys.stderr, or a log file of some sort.
            The server's documentation should include an explanation of how to configure this or where to find the recorded output.
            A server or gateway may supply different error streams to different applications, if this is desired.
        wsgi.multithread
            This value should evaluate true if the application object may be simultaneously invoked by another thread in the same process,
            and should evaluate false otherwise.
        wsgi.multiprocess
            This value should evaluate true if an equivalent application object may be simultaneously invoked by another process,
            and should evaluate false otherwise.
        wsgi.run_once
            This value should evaluate true if the server or gateway expects (but does not guarantee!) that the application will only be invoked this one time during the life of its containing process.
            Normally, this will only be true for a gateway based on CGI (or something similar).

        Finally, the environ dictionary may also contain server-defined variables.
        These variables should be named using only lower-case letters, numbers, dots, and underscores,
        and should be prefixed with a name that is unique to the defining server or gateway.
        For example, mod_python might define variables with names like mod_python.some_variable.

        Input and Error Streams
            The input and error streams provided by the server must support the following methods:
            Method 	        Stream 	Notes
            read(size) 	    input 	1
            readline() 	    input 	1, 2
            readlines(hint) input 	1, 3
            __iter__() 	    input
            flush() 	    errors 	4
            write(str) 	    errors
            writelines(seq) errors

            The semantics of each method are as documented in the Python Library Reference, except for these notes as listed in the table above:
            1.  The server is not required to read past the client's specified Content-Length,
                and should simulate an end-of-file condition if the application attempts to read past that point.
                The application should not attempt to read more data than is specified by the CONTENT_LENGTH variable.

                A server should allow read() to be called without an argument, and return the remainder of the client's input stream.

                A server should return empty bytestrings from any attempt to read from an empty or exhausted input stream.

            2.  Servers should support the optional "size" argument to readline(),
                but as in WSGI 1.0, they are allowed to omit support for it.

                (In WSGI 1.0, the size argument was not supported, on the grounds that it might have been complex to implement,
                and was not often used in practice... but then the cgi module started using it,
                and so practical servers had to start supporting it anyway!)

            3.  Note that the hint argument to readlines() is optional for both caller and implementer.
                The application is free not to supply it, and the server or gateway is free to ignore it.

            4.  Since the errors stream may not be rewound, servers and gateways are free to forward write operations immediately,
                without buffering. In this case, the flush() method may be a no-op.
                Portable applications, however, cannot assume that output is unbuffered or that flush() is a no-op.
                They must call flush() if they need to ensure that output has in fact been written.
                (For example, to minimize intermingling of data from multiple processes writing to the same error log.)

            The methods listed in the table above must be supported by all servers conforming to this specification.
            Applications conforming to this specification must not use any other methods or attributes of the input or errors objects.
            In particular, applications must not attempt to close these streams, even if they possess close() methods.

        :param environ:
        :type dict:
        :param start_response:
        :type function:
            :param status
            :type str
            :param response_headers
            :type [(header_name:str, header_value:str), ...]
            :return: write
            :rtype: function
                :param data
                :type bytestring
        :return: bytestring_iterator
        :rtype: iterable -> bytestrings
        """
        rq = self.make_request(environ)
        rv = self.dispatch_request(rq)
        if not isinstance(rv, tuple):
            rv = (200, rv)
        return self.make_response(rv[0], rv[1], start_response)

    def make_response(self, code, rv, start_response):
        return self.Response_class(code, rv, start_response=start_response)

    def add_routing(self, rule, handle):
        self.rules.add_rule(rule, handle)

    def dispatch_request(self, request):
        path = request.path
        handle = self.rules[path]
        if not handle:
            handle = self.not_found
        return handle(request=request)

    def not_found(self, *args, **kwargs):
        return 404, "not found"

    def make_request(self, environ):
        return self.Request_class(environ=environ)

    def send_static_file(self, file):
        return open(file, "rb")
