# coding=utf-8
import unittest
import response


class TestResponse(unittest.TestCase):
    def test_hello_world (self):
        resp = response.Response(200, "Hello, world").toBytes()
        resp = resp.decode("utf-8")
        print(resp)
        self.assertEqual(resp, "")
