from propeller.cookie import Cookie
from propeller.util.dict import ImmutableMultiDict, ImmutableDict

import time


class Request(object):
    def __init__(self, data='', ip=''):
        self.start_time = time.time()
        self.ip = ip
        self.method = '-'
        self.url = '-'
        self.protocol = '-'
        self.body = '-'

        if data:
            data = data.replace('\r', '')
            headers, self.body = data.split('\n\n')
            data = [d.strip() for d in data.split('\n')]
            self.method, url, self.protocol = data[0].split(' ')
            self.url, separator, querystring = url.partition('?')

            # Parse headers and cookies
            headers = []
            self.cookies = []
            for h in data[1:]:
                if not h:
                    break
                k, v = h.split(': ')
                if k == 'Cookie':
                    try:
                        cname, cval = v.split('=')
                    except ValueError:
                        pass
                    else:
                        self.cookies.append(Cookie(name=cname, value=cval))
                else:
                    headers.append((k, v))
            self.headers = ImmutableMultiDict(headers)

            # Parse GET variables
            self.get = self.__parse_request_data(querystring)

            # Parse POST data
            self.post = self.__parse_request_data(self.body)
        else:
            self.headers = ImmutableMultiDict()
            self.cookies = []
            self.get = ImmutableMultiDict()
            self.post = ImmutableMultiDict()

    def __parse_request_data(self, data):
        values = []
        for pair in data.split('&'):
            try:
                k, v = pair.split('=')
            except ValueError:
                pass
            else:
                values.append((k, v))
        return ImmutableMultiDict(values)

    @property
    def execution_time(self):
        return time.time() - self.start_time
