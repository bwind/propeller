from propeller.cookie import Cookie
from propeller.uploaded_file import UploadedFile
from propeller.util.dict import ImmutableMultiDict, ImmutableDict
from tempfile import SpooledTemporaryFile

import os
import re
import time
import urllib


class Request(object):
    def __init__(self, data=None, ip=''):
        self.start_time = time.time()
        self.ip = ip
        self.method = '-'
        self.url = '-'
        self.protocol = '-'
        self.body = ''
        self.data = data

        self.headers = ImmutableMultiDict()
        self.cookies = []
        self.files = []
        self.get = ImmutableMultiDict()
        self.post = ImmutableMultiDict()

        if self.data:
            self.data.seek(0)
            headers = []
            while True:
                header = self.data.readline().strip()
                if not header:
                    # Newline, which means end of HTTP headers.
                    break
                headers.append(header)

            self.method, url, self.protocol = headers[0].split(' ')
            self.url, separator, querystring = url.partition('?')

            # Parse headers and cookies
            self._parse_headers(headers)

            # Parse files
            #self._parse_files()

            # Parse GET variables
            self.get = self._parse_request_data(querystring, unquote=True)

            # Parse POST data
            #self.post = self._parse_request_data(self.data)

    def _parse_headers(self, headers):
        hdrs = []
        self.cookies = []
        for header in headers[1:]:
            if not header:
                # End of headers
                break
            field = header.split(': ')[0]
            value = header[header.index(': ') + 2:]
            fl = field.lower()
            if fl == 'x-real-ip' or fl == 'x-forwarded-for':
                self.ip = value.split(',')[0].strip()
            elif fl == 'cookie':
                try:
                    cname, cvalue = value.split('=')
                except ValueError:
                    pass
                else:
                    self.cookies.append(Cookie(name=cname, value=cvalue))
            else:
                hdrs.append((field, value))
        self.headers = ImmutableMultiDict(hdrs)

    def _parse_request_data(self, data, unquote=False):
        values = []
        for pair in data.split('&'):
            try:
                k, v = pair.split('=')
            except ValueError:
                pass
            else:
                if unquote:
                    v = urllib.unquote(v)
                values.append((k, v))
        return ImmutableMultiDict(values)

    def _parse_files(self):
        # Only parse files if we have a 'Content-Type' header with a
        # 'boundary' directive
        try:
            boundary = re.match(r'.*boundary=(.*)$',
                                self.headers['Content-Type'][0]).group(1)
        except Exception as e:
            if self.url == '/':
                print self.method
                print self.headers
                raise e
            return
        boundary = '--' + boundary
        boundary_end = boundary + '--'
        self.files = []
        self.data.seek(0)
        uploaded_file = None
        while True:
            line = self.data.readline().strip()
            if not line:
                # We've encountered a newline, and thus the end of the
                # HTTP headers.
                print '* END OF HEADERS'
                break
        while True:
            line = self.data.readline()
            if line.rstrip().startswith(boundary) and uploaded_file:
                print '* CLOSING FILE AT', self.data.tell()
                print len(line), line
                # End of a file.

                # Truncate the newline from this file, reset file
                # pointer of previous uploaded file and add to
                # self.files list.
                uploaded_file.file.seek(-2, os.SEEK_END)
                uploaded_file.file.truncate()
                uploaded_file.file.seek(0)
                self.files.append(uploaded_file)
                uploaded_file = None

            elif line.rstrip() == boundary:
                # Start of a new file. Parse headers of this multipart
                # and create new file.
                name = None
                filename = None
                mime_type = None
                while True:
                    header = self.data.readline().strip()
                    print '* MULTIPART HEADER:', header
                    if not header:
                        break
                    m = re.match(r'Content\-Disposition: form\-data; name="(.+)"; filename="(.+)"$', header)
                    if m:
                        name, filename = m.groups()
                    m = re.match(r'Content-Type: (.+)$', header)
                    if m:
                        mime_type = m.group(1)

                if name and filename and mime_type:
                    # Create new uploaded file
                    print '* CREATING NEW FILE'
                    uploaded_file = UploadedFile(name=name, filename=filename,
                                                 mime_type=mime_type)
                else:
                    print '* SOMETHING WENT WRONG:', name, filename, mime_type
            elif line.rstrip() == boundary_end:
                # EOF of POST body. We are done parsing files.
                print '* EOF POST'
                break
            else:
                if uploaded_file:
                    uploaded_file.file.write(line)
                else:
                    # Before the first boundary is an area that is
                    # ignored by MIME-compliant clients. This area is
                    # generally used to put a message to users of old
                    # non-MIME clients.
                    pass

    @property
    def execution_time(self):
        return time.time() - self.start_time
