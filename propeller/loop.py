import select
import socket


class _Loop(object):
    READ = 0x001
    WRITE = 0x004
    ERROR = 0x008 | 0x010

    def close_socket(self, sock):
        fd = sock.fileno()
        sock.close()
        if hasattr(self, '_sockets'):
            del self._sockets[fd]


class SelectLoop(_Loop):
    def __init__(self):
        self.readable = set()
        self.writeable = set()
        self.errors = set()

    def close_socket(self, sock):
        self.unregister(sock, self.READ)
        self.unregister(sock, self.WRITE)
        self.unregister(sock, self.ERROR)
        super(SelectLoop, self).close_socket(sock)

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
            events[r] = self.READ
        for w in writeable:
            events[w] = self.WRITE
        for e in errors:
            events[e] = self.ERROR
        return events.items()


class EpollLoop(_Loop):
    def __init__(self):
        self._epoll = select.epoll()
        self._sockets = {}

    def register(self, sock, event):
        if sock.fileno() not in self._sockets:
            self._sockets[sock.fileno()] = sock
        try:
            self._epoll.register(sock.fileno(), event)
        except IOError:
            pass

    def unregister(self, sock, event):
        self._epoll.unregister(sock.fileno())

    def poll(self):
        ret = {}
        events = self._epoll.poll()
        for e in events:
            ret[self._sockets[e[0]]] = e[1]
        return ret.items()


class KqueueLoop(_Loop):
    """KqueueLoop works on BSD style systems (FreeBSD, Mac OS). Faster
    than select.
    """
    def __init__(self):
        self._kqueue = select.kqueue()
        self._sockets = {}

    def register(self, sock, event):
        self._sockets[sock.fileno()] = sock
        self._control(sock.fileno(), event, select.KQ_EV_ADD)

    def unregister(self, sock, event=None):
        self._control(sock.fileno(), event, select.KQ_EV_DELETE)

    def _control(self, fd, event, flags):
        kevents = []
        if event & self.WRITE:
            kevents.append(select.kevent(fd, filter=select.KQ_FILTER_WRITE,
                                         flags=flags))
        if event & self.READ or not kevents:
            # Always read when there is not a write
            kevents.append(select.kevent(fd, filter=select.KQ_FILTER_READ,
                                         flags=flags))
        # Even though control() takes a list, it seems to return EINVAL
        # on Mac OS X (10.6) when there is more than one event in the list.
        for kevent in kevents:
            try:
                self._kqueue.control([kevent], 0)
            except OSError:
                pass

    def poll(self):
        kevents = self._kqueue.control(None, 1000)
        events = {}
        for e in kevents:
            fd = e.ident
            sock = self._sockets[fd]
            if e.filter == select.KQ_FILTER_READ:
                events[sock] = self.READ
            elif e.filter == select.KQ_FILTER_WRITE:
                if e.flags & select.KQ_EV_EOF:
                    # Report EOF as ERROR back to application, which
                    # results in closing the socket.
                    events[sock] = self.ERROR
                else:
                    events[sock] = self.WRITE
            elif e.flags & select.KQ_EV_ERROR:
                events[sock] = self.ERROR
        return events.items()


if hasattr(select, 'epoll'):
    Loop = EpollLoop
elif hasattr(select, 'kqueue'):
    Loop = KqueueLoop
else:
    # Fall back to select().
    Loop = SelectLoop
