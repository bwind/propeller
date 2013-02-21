class MultiDict(dict):
    def __init__(self):
        self._items = {}

    def __contains__(self, name):
        return name in self._items

    def __getitem__(self, name):
        return self._items[name]

    def __setitem__(self, name, value):
        if name != '_items':
            self._items[name] = [value]
        else:
            super(MultiDict, self).__setitem__(name, value)

    def __eq__(self, other):
        return other == self._items

    def __repr__(self):
        return repr(self._items)

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        for k in self._items:
            yield k

    def add(self, name, value):
        if name not in self._items:
            self._items[name] = []
        self._items[name].append(value)

    def items(self):
        return [(k, v) for k, values in self._items.items() for v in values]


class ImmutableMultiDict(MultiDict):
    def __init__(self, items=()):
        super(ImmutableMultiDict, self).__init__()
        for item in items:
            super(ImmutableMultiDict, self).add(item[0], item[1])

    __setitem__ = None
    add = None


class ImmutableDict(object):
    def __init__(self, items={}):
        self._items = items

    def __eq__(self, other):
        return other == self._items

    def __repr__(self):
        return repr(self._items)

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        for k in self._items.keys():
            yield k

    def items(self):
        return self._items.items()
