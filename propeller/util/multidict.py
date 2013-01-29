class MultiDict(object):
    def __init__(self):
        self.__items = {}

    def __contains__(self, name):
        return name in self.__items

    def __getitem__(self, name):
        return self.__items[name]

    def __setitem__(self, name, value):
        if name != '__items':
            self.__items[name] = [value]
        else:
            super(MultiDict, self).__setitem__(name, value)

    def add(self, name, value):
        if name not in self.__items:
            self.__items[name] = []
        self.__items[name].append(value)

    def items(self):
        return [(k, v) for k, values in self.__items.items() for v in values]
