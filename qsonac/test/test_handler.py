# coding=utf-8
import socket
import unittest

from config import Config

test_request = b"\r\n".join([
    b'GET / HTTP/1.1',
    b'Host: 192.168.1.68:48539'
    b'Connection: keep-alive',
    b'Cache-Control: max-age=0',
    b'Save-Data: on',
    b'User-Agent: Mozilla/5.0 (Linux; Android 6.0; M5 Note Build/MRA58K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3189.0 Mobile Safari/537.36',
    b'Upgrade-Insecure-Requests: 1',
    b'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    b'DNT: 1',
    b'Accept-Encoding: gzip, deflate',
    b'Accept-Language: en,es-ES;q=0.8,es;q=0.6,zh-CN;q=0.4,zh;q=0.2,zh-TW;q=0.2',
    b'\r\n'
])

test_request_len = len(test_request)


class TestHandler(unittest.TestCase):
    def test_server_has_recv_header(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((Config.host, Config.port))
        try:
            token = "server-had-to-responde-with-this"
            sock.sendall(f"GET / HTTP/1.1\r\nX-TEST: {token}\r\n\r\n".encode("ascii"))
            sock.shutdown(socket.SHUT_WR)
            chunks = []
            chunk = sock.recv(4096)
            while chunk:
                chunks.append(chunk)
                chunk = sock.recv(4096)
            response = b''.join(chunks).decode("utf-8")
            self.assertTrue(token in response)
            print(response)
        finally:
            sock.close()

    def test_timeout(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((Config.host, Config.port))
        try:
            chunks = []
            chunk = sock.recv(4096)
            while chunk:
                chunks.append(chunk)
                chunk = sock.recv(4096)
            response = b''.join(chunks).decode("utf-8")
            self.assertTrue("408" in response)
            print(response)
        finally:
            sock.close()

    def test_normal_request_with_explit_shutdown(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((Config.host, Config.port))
        try:
            total_sent = 0
            sent = sock.send(test_request)
            while total_sent < test_request_len:
                total_sent += sent
                sent = sock.send(test_request)
                if not sent:
                    raise RuntimeError("connection broken")
            sock.shutdown(socket.SHUT_WR)
            chunks = []
            chunk = sock.recv(4096)
            while chunk:
                chunks.append(chunk)
                chunk = sock.recv(4096)
            response = b''.join(chunks).decode("utf-8")
            self.assertTrue(
                '''{"HOST": " 192.168.1.6848539Connection keep-alive", "CACHE_CONTROL": " max-age=0", "SAVE_DATA": " on", "USER_AGENT": " Mozilla/5.0 (Linux; Android 6.0; M5 Note Build/MRA58K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3189.0 Mobile Safari/537.36", "UPGRADE_INSECURE_REQUESTS": " 1", "ACCEPT": " text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8", "DNT": " 1", "ACCEPT_ENCODING": " gzip, deflate", "ACCEPT_LANGUAGE": " en,es-ES;q=0.8,es;q=0.6,zh-CN;q=0.4,zh;q=0.2,zh-TW;q=0.2", "": ""}''' in response)
            print(response)
        finally:
            sock.close()

    def test_normal_request_without_explit_shutdown(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((Config.host, Config.port))
        try:
            total_sent = 0
            sent = sock.send(test_request)
            while total_sent < test_request_len:
                total_sent += sent
                sent = sock.send(test_request)
                if not sent:
                    raise RuntimeError("connection broken")
            # sock.shutdown(socket.SHUT_WR)
            chunks = []
            chunk = sock.recv(4096)
            while chunk:
                chunks.append(chunk)
                chunk = sock.recv(4096)
            response = b''.join(chunks).decode("utf-8")
            self.assertTrue(
                '''{"HOST": " 192.168.1.6848539Connection keep-alive", "CACHE_CONTROL": " max-age=0", "SAVE_DATA": " on", "USER_AGENT": " Mozilla/5.0 (Linux; Android 6.0; M5 Note Build/MRA58K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3189.0 Mobile Safari/537.36", "UPGRADE_INSECURE_REQUESTS": " 1", "ACCEPT": " text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8", "DNT": " 1", "ACCEPT_ENCODING": " gzip, deflate", "ACCEPT_LANGUAGE": " en,es-ES;q=0.8,es;q=0.6,zh-CN;q=0.4,zh;q=0.2,zh-TW;q=0.2", "": ""}''' in response)
            print(response)
        finally:
            sock.close()

            # def test_two_conn(self):
            #     sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #     sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #     try:
            #         sock2.connect((Config.host, Config.port))
            #         sock1.connect((Config.host, Config.port))
            #         totalsent1 = 0
            #         totalsent2 = 0
            #         while totalsent1 < test_request_len or totalsent2 < test_request_len:
            #             sent1 = sock1.send(test_request[totalsent1:])
            #             totalsent1 = totalsent1 + sent1
            #
            #             sent2 = sock1.send(test_request[totalsent2:])
            #             totalsent2 = totalsent2 + sent2
            #
            #         chunks = []
            #         chunk = sock1.recv(4096)
            #         while chunk:
            #             chunks.append(chunk)
            #             chunk = sock1.recv(4096)
            #         response = b''.join(chunks).decode("utf-8")
            #         print(response)
            #     finally:
            #         sock1.close()
            #         sock2.close()
