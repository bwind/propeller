class MultiDict(object):
    def __init__(self):
        self.__items = []

    def __getitem__(self, name):
        found = []
        for k, v in self.__items:
            if k == name:
                found.append(v)
        return found

    def __setitem__(self, name, value):
        if name != '__items':
            self.__items.append((name, value))
        else:
            super(MultiDict, self).__setitem__(name, value)

    def items(self):
        return self.__items
