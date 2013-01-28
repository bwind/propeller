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
                                                    self.readable)

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
        self._kqueue = select.kqueue()
        self._active = {}

    def close(self):
        self._kqueue.close()
        self._active = {}

    def register(self, sock, events):
        self._active[sock.fileno()] = sock
        self._control(sock.fileno(), events, select.KQ_EV_ADD)

    def unregister(self, sock, events=None):
        self._control(sock.fileno(), events, select.KQ_EV_DELETE)

    def _control(self, fd, events, flags):
        kevents = []
        if events & Loop.WRITE:
            kevents.append(select.kevent(fd, filter=select.KQ_FILTER_WRITE,
                                         flags=flags))
        if events & Loop.READ or not kevents:
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
            sock = self._active[fd]
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

        """
        kevents = self._kqueue.control(None, 1000)
        events = {}
        for kevent in kevents:
            fd = kevent.ident
            if kevent.filter == select.KQ_FILTER_READ:
                events[fd] = events.get(fd, 0) | Loop.READ
            if kevent.filter == select.KQ_FILTER_WRITE:
                if kevent.flags & select.KQ_EV_EOF:
                    # If an asynchronous connection is refused, kqueue
                    # returns a write event with the EOF flag set.
                    # Turn this into an error for consistency with the
                    # other IOLoop implementations.
                    # Note that for read events, EOF may be returned before
                    # all data has been consumed from the socket buffer,
                    # so we only check for EOF on write events.
                    events[fd] = Loop.ERROR
                else:
                    events[fd] = events.get(fd, 0) | Loop.WRITE
            if kevent.flags & select.KQ_EV_ERROR:
                events[fd] = events.get(fd, 0) | Loop.ERROR
        return events.items()
        """

if hasattr(select, 'kqueue'):
    Loop = KqueueLoop
else:
    """Fall back to select().
    """
    Loop = SelectLoop
