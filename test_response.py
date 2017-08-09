# coding=utf-8
import unittest
import response
from config import Config


class TestResponse(unittest.TestCase):
    def test_hello_world (self):
        resp = b''
        for chunk in response.Response(200, Config.message):
            resp += chunk
            print(chunk.decode("utf-8"))
        resp = resp.decode("utf-8")
        print(resp)
        self.assertEqual(resp, "")
