# coding=utf-8
from unittest import TestCase
from qsonac.urlmap import TreeMap


class TestTreeMap(TestCase):
    def test_start_with_no_member (self):
        tree1 = TreeMap()
        self.assertEqual(tree1.parent, None)
        self.assertEqual(len(tree1), 0)
        self.assertFalse("not in" in tree1)
        with self.assertRaises(KeyError):
            errror = tree1["no exist"]
        tree1["/first_key"] = "/first_key_first_value"
        self.assertEqual(len(tree1), 1)
        self.assertEqual(tree1["/first_key"], "/first_key_first_value")
        tree1["/first_key"] = "/first_key_second_value"
        self.assertEqual(len(tree1), 1)
        self.assertEqual(tree1["/first_key"], "/first_key_second_value")
        self.assertEqual(tree1.parent, None)
        self.assertEqual(len(tree1.children), 0)
        with self.assertRaises(KeyError):
            errror = tree1[None]
        with self.assertRaises(KeyError):
            tree1[None] = "error"
        self.assertEqual(len(tree1.children), 0)
        self.assertEqual(tree1.parent, None)
        tree2 = TreeMap()
        with self.assertRaises(KeyError):
            tree2[None] = "/"
        self.assertEqual(tree1.parent, None)
        self.assertEqual(len(tree1.children), 0)
        self.assertFalse(tree1 in tree2)
        tree2["/"] = ""
        self.assertTrue(tree1 in tree2)
        tree3 = TreeMap("/tq", "asdfasd")
        tree4 = TreeMap("not/tq", "asdfasd")
        self.assertTrue(tree3 in tree2)
        self.assertFalse(tree4 in tree2)
        self.assertFalse(tree2 in tree3)

    def test_two (self):
        tree = TreeMap()
        tree["/"] = 1
        tree["/a"] = 2
        self.assertEqual(tree["/a"], 2)
