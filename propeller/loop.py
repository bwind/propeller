import select


class _Loop(object):
    READ = 0x001
    WRITE = 0x004
    ERROR = 0x008 | 0x010

class SelectLoop(_Loop):
    def __init__(self):
        self.readable = []
        self.writeable = []
        self.errors = []

    """
    def register(self, fd, event):
        if event & self.READ:
            self.readable.append(fd)
        elif event & self.WRITE:
            self.writeable.append(fd)
        elif event & self.ERROR:
            self.errors.append(fd)

    def unregister(self, fd):
        if fd in self.readable:
            self.readable.remove(fd)
        if fd in self.writeable:
            self.writeable.remove(fd)
        if fd in self.errors:
            self.errors.remove(fd)

    def poll(self):
        readable, writeable, errors = select.select(self.readable,
                                                    self.writeable,
                                                    self.errors)
        return (readable, writeable, errors)
    """

#if hasattr(select, 'kqueue'):
#    Loop = KqueueLoop
#else:
Loop = SelectLoop
