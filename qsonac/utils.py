# coding=utf-8
class _Miss:
    pass


missing = _Miss()


class cached_property(property):
    """
    A decorator that converts a function into a lazy property.  The
    function wrapped is called the first time to retrieve the result
    and then that calculated result is used the next time you access
    the value::

        class Foo(object):

            @cached_property
            def foo(self):
                # calculate something important here
                return 42

    The class has to have a `__dict__` in order for this property to
    work.
    """

    # implementation detail: A subclass of python's builtin property
    # decorator, we override __get__ to check for a cached value. If one
    # choses to invoke __get__ by hand the property will still work as
    # expected because the lookup logic is replicated in __get__ for
    # manual invocation.

    def __init__(self, func, name = None, doc = None):
        super(self.__class__, self).__init__(func)
        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.__doc__ = doc or func.__doc__
        self.func = func

    def __set__(self, obj, value):
        obj.__dict__[self.__name__] = value

    def __get__(self, obj, type = None):
        if obj is None:
            return self
        value = obj.__dict__.get(self.__name__, missing)
        if value is missing:
            value = self.func(obj)
            obj.__dict__[self.__name__] = value
        return value

