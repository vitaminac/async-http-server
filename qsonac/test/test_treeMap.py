# coding=utf-8
from unittest import TestCase
from qsonac.urlmap import TreeMap


class TestTreeMap(TestCase):
    def test_start_with_no_member (self):
        t = TreeMap()
        self.assertEqual(len(t), 0)
        self.assertFalse("q" in t)
        with self.assertRaises(KeyError):
            q = t["no exist"]
        t["ss"] = "///qqqq"
        self.assertEqual(len(t), 1)
        self.assertEqual(t["ss"], "///qqqq")
        t["ss"] = "///qqqw"
        self.assertEqual(len(t), 1)
        self.assertEqual(t["ss"], "///qqqw")
        self.assertEqual(t.parent, None)
        self.assertEqual(len(t.children), 0)
        with self.assertRaises(KeyError):
            q = t[None]
        with self.assertRaises(KeyError):
            t[None] = "v"
        self.assertEqual(len(t.children), 0)
        tt = TreeMap()
        with self.assertRaises(KeyError):
            tt[None] = "//"
        self.assertEqual(len(t.children), 0)
        self.assertFalse(t in tt)
        tt["s"] = "q"
        self.assertTrue(t in tt)
        ttt = TreeMap("tq", "asdfasd")
        self.assertFalse(ttt in tt)
        self.assertFalse(tt in ttt)
