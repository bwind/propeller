import select
import socket


class _Loop(object):
    READ = 0x001
    WRITE = 0x004
    ERROR = 0x008 | 0x010


class SelectLoop(_Loop):
    def __init__(self):
        self.readable = set()
        self.writeable = set()
        self.errors = set()

    def close_socket(self, sock):
        self.unregister(sock, Loop.READ)
        self.unregister(sock, Loop.WRITE)
        self.unregister(sock, Loop.ERROR)
        sock.close()

    def register(self, sock, event):
        if event & self.READ:
            self.readable.add(sock)
        elif event & self.WRITE:
            self.writeable.add(sock)
        elif event & self.ERROR:
            self.errors.add(sock)

    def unregister(self, sock, event):
        if event & self.READ:
            self.readable.discard(sock)
        elif event & self.WRITE:
            self.writeable.discard(sock)
        elif event & self.ERROR:
            self.errors.discard(sock)

    def poll(self):
        readable, writeable, errors = select.select(self.readable,
                                                    self.writeable,
                                                    self.errors)

        events = {}
        for r in readable:
            events[r] = Loop.READ
        for w in writeable:
            events[w] = Loop.WRITE
        for e in errors:
            events[e] = Loop.ERROR
        return events.items()


class KqueueLoop(_Loop):
    def __init__(self):
        self.__kqueue = select.kqueue()
        self.__sockets = {}

    def get_sockets(self):
        return self.__sockets

    def close_socket(self, sock):
        fd = sock.fileno()
        sock.close()
        del self.__sockets[fd]

    def register(self, sock, event):
        self.__sockets[sock.fileno()] = sock
        self.__control(sock.fileno(), event, select.KQ_EV_ADD)

    def unregister(self, sock, event=None):
        self.__control(sock.fileno(), event, select.KQ_EV_DELETE)

    def __control(self, fd, event, flags):
        kevents = []
        if event & Loop.WRITE:
            kevents.append(select.kevent(fd, filter=select.KQ_FILTER_WRITE,
                                         flags=flags))
        if event & Loop.READ or not kevents:
            # Always read when there is not a write
            kevents.append(select.kevent(fd, filter=select.KQ_FILTER_READ,
                                         flags=flags))
        # Even though control() takes a list, it seems to return EINVAL
        # on Mac OS X (10.6) when there is more than one event in the list.
        for kevent in kevents:
            try:
                self.__kqueue.control([kevent], 0)
            except OSError:
                pass

    def poll(self):
        kevents = self.__kqueue.control(None, 1000)
        events = {}
        for e in kevents:
            fd = e.ident
            sock = self.__sockets[fd]
            if e.filter == select.KQ_FILTER_READ:
                events[sock] = Loop.READ
            elif e.filter == select.KQ_FILTER_WRITE:
                if e.flags & select.KQ_EV_EOF:
                    events[sock] = Loop.ERROR
                else:
                    events[sock] = Loop.WRITE
            elif e.flags & select.KQ_EV_ERROR:
                events[sock] = Loop.ERROR
        return events.items()


if hasattr(select, 'kqueue'):
    Loop = KqueueLoop
else:
    """Fall back to select().
    """
    Loop = SelectLoop
