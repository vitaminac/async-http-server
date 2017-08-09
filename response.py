# coding=utf-8
import io
from email.utils import formatdate
from string import Template

from status_codes import codes


class Body:
    def __init__ (self, body, *args, **kwargs):
        if isinstance(body, str):
            self.encoding = kwargs["encoding"]
            body = body.encode(self.encoding)
            self.io_raw_stream = io.BytesIO(body)

    def __len__ (self):
        current_position = self.io_raw_stream.tell()
        self.io_raw_stream.seek(0, io.SEEK_END)
        length = self.io_raw_stream.tell()
        self.io_raw_stream.seek(current_position, io.SEEK_SET)
        return length

    def __iter__ (self):
        return self.io_raw_stream


class Response:
    response_http_header_template = Template('''HTTP/$http_protocol_version $code $status\n$headers\n\n''')

    content_type_template = Template('''$type; charset=$encoding''')

    header_template = Template('''$header_field: $value''')

    def __init__ (self, status_code: int, body = "", headers: dict = None, encoding: str = "utf-8", mimetype: str = "text/plain", protocol_version: float = 1.1):
        # cant set headers to default argument's value
        if not headers:
            headers = { }
        self.raw_data = Body(body, encoding=encoding)
        self.headers = {
            "Content-Type"  : Response.content_type_template.safe_substitute({
                "type"    : mimetype,
                "encoding": encoding
            }),
            # The length of the request body in octets (8-bit bytes).
            "Content-Length": str(len(self.raw_data)),
            "Date"          : formatdate(timeval=None, localtime=False, usegmt=True),
            "Server"        : "socket server"
        }
        self.headers.update(headers)
        self.http_args = {
            "http_protocol_version": str(protocol_version),
            "code"                 : "404",
            "status"               : codes["404"],
            "headers"              : self.generate_headers(self.headers)
        }
        self.http_head = Response.response_http_header_template.safe_substitute(self.http_args)

    def generate_headers (self, headers: dict):
        return "\n".join([Response.header_template.safe_substitute({
            "header_field": k,
            "value"       : v
        }) for k, v in headers.items()])

    def __str__ (self) -> str:
        return self.http_head

    def __repr__ (self) -> str:
        return self.__str__()

    def toBytes (self):
        return self.__str__().encode("ascii")

    def __iter__ (self):
        return self

    def __next__ (self):
        return self.http_head

    def __call__ (self, *args, **kwargs):
        return self.http_head
