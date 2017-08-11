# coding=utf-8

from typing import Callable
from collections import MutableMapping


class TreeMap(MutableMapping):
    # a restrict TreeMap, for URLMapping
    # create a restrict TreeMap and store compatible key, value pair inside Tree
    # how is compatible is abstracted, that should be defined in each subclass
    # I mean, if we defined a new key, value is compatible with TreeMao T when key is start with T' root key, or vice versa
    # for example T's root key is "/", then "/abc" is compatible, and "abc" no
    # but there is always a exception: a empty tree is always compatible with any TreeMap, although it doesnt contain any

    # Specification
    # Each TreeMap contains a root, a parent reference and a list of subtree (another instance of TreeMap)
    # the top node of entire tree , root has not parent, root can be None, see below

    # tree.root return the highest node of the current tree, if tree.root is None, this mean that this tree is empty,
    # this can be in case when create map without specific key, value

    # compute key in tree, will check if tree can contains the specific key with no exact search,
    # any key in empty tree must return false
    # subtree in tree, check if tree contain the subtree, any tree always contains empty subtree, if subtree is not empty
    # it will check if the root of subtree can be contain in the tree

    # tree[key] return value associated with specific key, no exact search,
    # it will return the root of lowest subtree that { key in subtree } will compute to true, repeat: it's not a exact search

    # tree[key] = value, if key is compatible with this tree and key in subtree[key] with < exact search >!! return true,
    # then replace it root value with new value, if not found create new node of key, value pair
    # if key is compatible but can be contained in tree,
    # it mean than new key should be new root and current root should be his child
    # otherwise raise a KeyError exception
    # in the case then tree is empty, then initialize with this new key, value

    # del tree[key] delete the specific node that exactly match the key, including the root node
    # normally its subtree wont be eliminate, its subtree will be reconstructed and link to parent of eliminated node
    # but if subtree doesnt have parent, this mean that the subtree is entire tree, and it locate at root of all node
    # this cause a undefined behavior

    # len(TreeMap) return the current node inside the tree, 0 if empty
    class Node:
        def __init__ (self, key, value):
            self._key = key
            self.value = value

        def __eq__ (self, other):
            if hasattr(other, 'key'):
                return other.key == self.key and other.value == self.value
            return False

        def __hash__ (self):
            return self.key

        @property
        def key (self):
            return self._key

    def __init__ (self, root_key = None, value = None, parent = None):
        if root_key is None:
            self.root = None
            self.length = 0
        else:
            self.root = self.Node(root_key, value)
            self.length = 1
        self.parent = parent
        self.children = set()

    def __eq__ (self, other):
        pass

    def _find (self, key):
        # return last subtree that contain the key
        if key in self:
            if key == self.root.key:
                return self
            else:
                for subtree in self.children:
                    if key in subtree:
                        return subtree._find(key)
            # no exact match found, return the last match
            return self
        # not found
        raise KeyError

    def __getitem__ (self, key):
        # raise KeyError if not found
        tree = self._find(key)
        return tree.root.value

    # implementation detail, exchange the current root tree with newly root tree
    def _exchange (self, other):
        if isinstance(other, TreeMap):
            # exchange root node
            temp = other.root
            other.root = self.root
            self.root = temp
            # exchange parent
            temp = other.parent
            other.parent = self.parent
            self.parent = temp
            # exchange children
            temp = other.children
            other.children = self.children
            self.children = temp
            # exchange length
            temp = other.length
            other.length = self.length
            self.length = temp

    def __validate_key (self, key):
        return key is not None

    def __setitem__ (self, key, value):
        try:
            tree = self._find(key)
            # exact key found, replace with new value
            if tree.root.key == key:
                tree.root.value = value
            # not exact node found, create a new subtree
            else:
                subtree = TreeMap(key, value, self)
                tree.children.add(subtree)
                # reorganize children of parent tree
                # check if has some can be merge into new create subtree
                for child in tree:
                    pass

        except KeyError:
            if self.__validate_key(key):
                # check if compatible
                new_root_tree = TreeMap(key, value)
                if not self.root:
                    self._exchange(new_root_tree)
                    return
                elif self.root.key in new_root_tree:
                    # key is compatible
                    # make this as parent of current root tree
                    new_root_tree.children.add(self)
                    self.parent = new_root_tree
                    # automatically convert current instance be the new root
                    self._exchange(new_root_tree)
                    return

            # not compatible
            raise

    def iter (self):
        yield self.root.key
        for child in self.children:
            yield from child

    def __iter__ (self):
        return self.iter()

    def __len__ (self):
        return self.length

    def __delitem__ (self, key):
        if key:  # check if key is not "", that will be default root of tree
            tree = self._find(key)
            # found
            if tree.root.key == key:
                parent = tree.parent
                # link his children to parent
                parent.children.update(tree.children)
                parent.children.remove()

    def __str__ (self):
        return str(self.root.key)

    def __can_contains (self, key):
        return key.startswith(self.root.key)

    def __contains__ (self, key):
        # this may be override when subclassing
        # standard str compare
        # "/" in "/abc", "/"-parent -> "/abc"-child
        # "/abc" in "/" -> true
        # "/" in "/" -> true
        # "/aaa" in "aab" -> false

        if self.__validate_key(key):
            # if key is subtree, check if subtree can be contained in tree
            if isinstance(key, TreeMap) and key.root is None:
                # subtree is empty return true
                if self.root is None:
                    return True
                    # else compare key
            key = str(key)
            return self.root is not None and self.__can_contains(key)
        else:
            raise KeyError


class URLMap(TreeMap):
    def __init__ (self, root_key: str = "/", value: Callable = None, parent = None):
        super(self.__class__, self).__init__(root_key, value, parent)

    def __validate_key (self, key):
        return super(self.__class__, self).__validate_key(key) and key.startswith("/")

    def add_rule (self, rule: str, handle: Callable = None):
        self[rule] = handle

    def __setitem__ (self, key: str, value: Callable = None):
        return super(self.__class__, self).__setitem__(key, value)
