from propeller.util.dict import ImmutableMultiDict, ImmutableDict

import time


class Request(object):
    method = '-'
    url = '-'
    protocol = None

    def __init__(self, data='', ip=''):
        self.start_time = time.time()
        self.ip = ip
        if data:
            data = [d.strip() for d in data.split('\n')]
            self.method, self.url, self.protocol = data[0].split(' ')

            # Parse headers
            headers = []
            cookies = {}
            for h in data[1:]:
                if not h:
                    break
                k, v = h.split(': ')
                if k == 'Cookie':
                    cname, cval = v.split('=')
                    cookies[cname] = cval
                else:
                    headers.append((k, v))
            self.headers = ImmutableMultiDict(headers)
            self.cookies = ImmutableDict(cookies)
        else:
            self.headers = ImmutableMultiDict()
            self.cookies = ImmutableDict()

    @property
    def execution_time(self):
        return time.time() - self.start_time
