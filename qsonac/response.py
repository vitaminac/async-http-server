# coding=utf-8
import io
from string import Template
from typing import Any, Callable, List, Tuple

from qsonac.status_codes import codes


class Body:
    def __init__(self, body, *args, **kwargs):
        if isinstance(body, str):
            self.encoding = kwargs["encoding"]
            body = body.encode(self.encoding)
            body = io.BytesIO(body)
        if isinstance(body, io.IOBase):
            self.io_raw_stream = body
            current_position = self.io_raw_stream.tell()
            self.io_raw_stream.seek(0, io.SEEK_END)
            self.length = self.io_raw_stream.tell()
            self.io_raw_stream.seek(current_position, io.SEEK_SET)

    def __len__(self):
        return self.length

    def __iter__(self):
        return self

    def close(self):
        self.io_raw_stream.close()

    def __next__(self):
        bytes = self.io_raw_stream.read(2048)
        if bytes:
            return bytes
        else:
            self.close()
            raise StopIteration


class Response:
    response_http_header_template = Template('''HTTP/$http_protocol_version $status\n$headers\n\n''')

    status_template = Template('''$code $status''')

    header_template = Template('''$header_field: $value''')

    def __init__(self, status_code: int, body = "", headers: dict = None, encoding: str = "utf-8", mimetype: str = "text/html", protocol_version: float = 1.1,
                 start_response: Callable[[str, List[Tuple[str, str]], Any], Callable[[bytes], Any]] = None, conn_close = True):
        # cant set headers to default argument's value
        if not headers:
            headers = { }
        self.body = Body(body, encoding=encoding)
        self.headers = {
            # If a Content-Type header field is not present, the recipient MAY either assume a media type of application/octet-stream (RFC2046, Section 4.5.1) or examine the data to determine its type
            "Content-Type"  : f"{mimetype}; charset={encoding}",
            # The length of the request body in octets (8-bit bytes).
            "Content-Length": str(len(self.body)),
            "Connection"    : "close" if conn_close else "keep-alive"
        }
        self.headers.update(headers)
        self.http_args = {
            "http_protocol_version": str(protocol_version),
            "status"               : self.status_template.safe_substitute({
                "code"  : status_code,
                "status": codes[str(status_code)]
            }),
            "headers"              : self.generate_headers(self.headers)
        }
        self.http_head = Response.response_http_header_template.safe_substitute(self.http_args).encode("ascii")
        self.start_response = start_response
        if start_response:
            start_response(self.http_args["status"], list(self.headers.items()))

    def generate_headers(self, headers: dict):
        return "\n".join([Response.header_template.safe_substitute({
            "header_field": k,
            "value"       : v
        }) for k, v in headers.items()])

    def close(self):
        self.body.close()

    def __str__(self) -> str:
        return self.http_head

    def __repr__(self) -> str:
        return self.__str__()

    def __iter__(self):
        if not self.start_response:
            yield self.http_head
        for chunk in self.body:
            yield chunk

    def __call__(self, *args, **kwargs):
        return self.__iter__()
