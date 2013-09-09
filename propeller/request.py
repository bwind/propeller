from propeller.cookie import Cookie
from propeller.multipart import MultiPartParser
from propeller.util.dict import MultiDict, ImmutableMultiDict, ImmutableDict
from tempfile import SpooledTemporaryFile

import os
import re
import time
import urllib
import Queue


class Request(object):
    def __init__(self, ip='', sock=None):
        self.ip = ip
        self.method = '-'
        self.path = '-'
        self.url = '-'
        self.protocol = '-'
        self.body = ''

        self._sock = sock
        self._input = SpooledTemporaryFile(max_size=1024 * 1024 * 2)
        self._output = Queue.Queue()
        self._bytes = 0
        self._content_length = 0
        self._header_data = ''

        self.headers = ImmutableMultiDict()
        self.cookies = []
        self.files = []
        self.get = ImmutableMultiDict()
        self.post = ImmutableMultiDict()

    def _parse(self):
        if self._input:
            self._input.seek(0)
            self.method, self.path, self.protocol = self._input.readline().split(' ')
            self.url, separator, querystring = self.path.partition('?')

            # Parse headers and cookies
            self.headers, self.cookies = self._parse_headers_and_cookies()

            # Parse POST and FILES
            parser = MultiPartParser(self)
            self.post, self.files = parser._parse_post_and_files()

            # Parse GET
            self.get = self._parse_request_data(querystring)

    def _has_more_data(self):
        return self._message_bytes < self._content_length

    @property
    def _message_bytes(self):
        return self._bytes - self._get_message_start()

    def _get_message_start(self):
        try:
            return self._header_data.index('\r\n\r\n') + 4
        except:
            return 0

    def _write(self, data):
        self._bytes += len(data)
        self._input.write(data)

        # Only accummulate up to 16kb of possible header data
        if len(self._header_data) < 2 ** 14:
            self._header_data += data
            match = re.search('content\-length: ([0-9]+)', self._header_data.lower())
            if match:
                # TODO: does not apply for HEAD requests
                self._content_length = int(match.group(1))

    def _parse_headers_and_cookies(self):
        self._input.seek(0)
        headers = []
        cookies = []
        # Skip first line
        self._input.readline()
        while True:
            header = self._input.readline().strip()
            if not header:
                # Newline, which means end of HTTP headers.
                break
            field = header.split(': ')[0]
            try:
                value = header[header.index(': ') + 2:]
            except:
                continue
            fl = field.lower()
            if fl == 'x-real-ip' or fl == 'x-forwarded-for':
                self.ip = value.split(',')[0].strip()
            elif fl == 'cookie':
                for cpair in value.split(';'):
                    try:
                        cname, cvalue = cpair.strip().split('=')
                    except ValueError:
                        pass
                    else:
                        cookies.append(Cookie(name=cname, value=cvalue))
            else:
                headers.append((field, value))
        return (ImmutableMultiDict(headers), cookies)

    def _parse_request_data(self, data):
        values = []
        for pair in data.split('&'):
            try:
                k, v = pair.split('=')
            except ValueError:
                pass
            else:
                v = urllib.unquote_plus(v)
                values.append((k, v))
        return ImmutableMultiDict(values)

    @property
    def _execution_time(self):
        try:
            return time.time() - self._start_time
        except:
            return 0
