# coding=utf-8

from collections import MutableMapping


class Headers(MutableMapping, dict):
    """
    Read only version of the headers from a WSGI environment.  This
    provides the same interface as `Headers` and is constructed from
    a WSGI environment.
    """

    def __init__(self, environ: dict):
        super(self.__class__, self).__init__()
        self.environ = environ

    def __iter__(self):
        for key in self.environ:
            if key.startswith('HTTP_'):
                yield key[5:].replace('_', '-').title()
            elif key in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                yield key.replace('_', '-').title()

    def __len__(self):
        # the iter is necessary because otherwise list calls our
        # len which would call list again and so forth.
        return len(list(iter(self)))

    def __getitem__(self, key):
        # _get_mode is a no-op for this class as there is no index but
        # used because get() calls it.
        key = key.upper().replace('-', '_')
        if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            key = 'HTTP_' + key
        return self.environ[key]

    def __str__(self):
        return f"{{{(','.join(['%s:%s' % header for header in self.items()]))}}}"

    def __repr__(self):
        return self.__str__()

    def __delitem__(self, key):
        pass

    def __setitem__(self, key, value):
        pass
