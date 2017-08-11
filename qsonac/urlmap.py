# coding=utf-8

from typing import Callable


class TreeMap:
    # TreeMap
    # Each TreeMap contains a root, a parent reference and a list of subtree (another instance of TreeMap)
    # specification
    # key in tree, check if tree contain the item, no exact search
    # tree[key] return value associated with specific key, no exact search, it will return the root of lowest subtree that item in subtree will compute to true, repeat: it's not a exact search
    # tree[key] = value, if key in subtree[key] with [[exact search]]!! return true, replace it root value with new value, if not add new node of key, value pair
    class Node:
        def __init__ (self, key, value):
            self.key = key
            self.value = value

    def __init__ (self, key = "", value = None, parent = None):
        self._root = self.Node(key, value)
        self.parent = parent
        self.children = []

    @property
    def root (self):
        return self._root.value

    @property
    def key (self):
        return self._root.key

    def __hash__ (self):
        hash(self.key)

    def __eq__ (self, other):
        if hasattr(other, 'key'):
            return other.key == self.key or other == self.key
        return other == self.key

    def __getitem__ (self, key):
        # return closest node
        if key in self:
            if key == self:
                return self.root
            else:
                for subtree in self.children:
                    if key in subtree:
                        return subtree[key]
            # no exact match found, return the last match
            return self.root
        return None

    def __setitem__ (self, key, value):
        # replace with new value
        if key == self:
            self._root.value = value
            return

        for subtree in self.children:
            if key in subtree:
                subtree[key] = value
                return

        # not in any child of current list, create a new subtree
        subtree = TreeMap(key, value, self)
        self.children.append(subtree)

    def __contains__ (self, key):
        # this may be override when subclassing
        # standard str compare
        # "/abc" in "/" -> true
        # "/" in "/" -> true
        # "/aaa" in "aab" -> false
        return self.key in key and (key > self.key or key == self.key)


class URLMap(TreeMap):
    def __init__ (self, key: str = "", value: Callable = None, parent = None):
        super(self.__class__, self).__init__(key, value, parent)

    def add_rule (self, rule: str, handle):
        if not rule.startswith("/"):
            raise Exception("not start with slash")
        self[rule] = handle
