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
        self.body = ''

        if data:
            data = data.replace('\r', '')
            headers, self.body = data.split('\n\n')
            headers = [d.strip() for d in headers.split('\n')]
            self.method, url, self.protocol = headers[0].split(' ')
            self.url, separator, querystring = url.partition('?')

            # Parse headers and cookies
            hdrs = []
            self.cookies = []
            for h in headers[1:]:
                if not h:
                    break
                k, v = h.split(': ')
                if k.lower() == 'x-real-ip' or k.lower() == 'x-forwarded-for':
                    self.ip = v.split(',')[0].strip()
                elif k.lower() == 'cookie':
                    try:
                        cname, cval = v.split('=')
                    except ValueError:
                        pass
                    else:
                        self.cookies.append(Cookie(name=cname, value=cval))
                else:
                    hdrs.append((k, v))
            self.headers = ImmutableMultiDict(hdrs)

            # Parse GET variables
            self.get = self._parse_request_data(querystring)

            # Parse POST data
            self.post = self._parse_request_data(self.body)

            # Parse files
            self.files = self._parse_files()
        else:
            self.headers = ImmutableMultiDict()
            self.cookies = []
            self.get = ImmutableMultiDict()
            self.post = ImmutableMultiDict()

    def _parse_request_data(self, data):
        values = []
        for pair in data.split('&'):
            try:
                k, v = pair.split('=')
            except ValueError:
                pass
            else:
                values.append((k, v))
        return ImmutableMultiDict(values)

    def _parse_files(self):
        pass

    @property
    def execution_time(self):
        return time.time() - self.start_time
