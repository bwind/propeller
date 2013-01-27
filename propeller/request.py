from propeller.util.multidict import MultiDict

import time


class Request(object):
    def __init__(self, data):
        self.start_time = time.time()
        data = [d.strip() for d in data.split('\n')]
        self.method, self.url, self.protocol = data[0].split(' ')

        # Parse headers
        self.headers = MultiDict()
        for h in data[1:]:
            if not h:
                break
            k, v = h.split(': ')
            self.headers[k] = v

    @property
    def execution_time(self):
        return time.time() - self.start_time
