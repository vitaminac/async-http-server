# coding=utf-8
import socket
import unittest

from config import Config


class TestHandler(unittest.TestCase):
    # def test_timeout(self):
    #     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     sock.connect((Config.host, Config.port))
    #     try:
    #         chunks = []
    #         chunk = sock.recv(4096)
    #         while chunk:
    #             chunks.append(chunk)
    #             chunk = sock.recv(4096)
    #         response = b''.join(chunks).decode("utf-8")
    #         self.assertTrue("408" in response)
    #         print(response)
    #     except Exception as e:
    #         print(e)
    #     finally:
    #         sock.close()

    def test_server_has_recv_header(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((Config.host, Config.port))
        try:
            token = "server-had-to-responde-with-this"
            sock.sendall(f"GET / HTTP/1.1\r\nX-TEST: {token}\r\n\r\n".encode("ascii"))
            chunks = []
            chunk = sock.recv(4096)
            while chunk:
                chunks.append(chunk)
                chunk = sock.recv(4096)
            response = b''.join(chunks).decode("utf-8")
            self.assertTrue(token in response)
            print(response)
        except Exception as e:
            print(e)
        finally:
            sock.close()
