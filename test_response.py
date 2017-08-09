# coding=utf-8
import unittest
import response
from config import Config
import re


class TestResponse(unittest.TestCase):
    pattern = re.compile(r"HTTP/\d.?\d? \d+ \w+\n([^:]+:[^\n]+\n)+\n.+")

    def test_hello_world (self):
        resp = b''
        for chunk in response.Response(200, Config.message):
            resp += chunk
            print(chunk.decode("utf-8"))
        resp = resp.decode("utf-8")
        print(resp)
        self.assertTrue(TestResponse.pattern.match(resp))
