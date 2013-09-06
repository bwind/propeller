from propeller.uploaded_file import UploadedFile
from propeller.util.dict import MultiDict, ImmutableMultiDict

import re
import urllib


class MultiPartParser(object):
    def __init__(self, request):
        self._request = request

    def _parse_post_and_files(self):
        ib = self._request._input
        ib.seek(0)
        # Only parse files if we have a 'Content-Type' header with a
        # 'boundary' directive
        try:
            boundary = re.match(r'.*boundary=(.*)$',
                                self._request.headers['Content-Type'][0]).group(1)
        except Exception as e:
            # Skip headers
            while True:
                if not ib.readline().strip():
                    break
            values = []
            for pair in ib.read().split('&'):
                try:
                    k, v = pair.split('=')
                except ValueError:
                    pass
                else:
                    v = urllib.unquote_plus(v)
                    values.append((k, v))
            return (ImmutableMultiDict(values), [])

        # Iterables we're going to return
        post = MultiDict()
        files = []

        boundary = '--' + boundary
        uploaded_file = None
        post_value = None
        chunk_size = 4096

        name, filename, mime_type = None, None, None

        while True:
            if not ib.readline().strip():
                # We've encountered a newline, and thus the end of the
                # HTTP headers.
                break

        while True:
            chunk = ib.read(chunk_size)

            if not chunk:
                # We're done reading
                break

            elif boundary in chunk:
                # We've encountered a new mime part, or the boundary end.
                # Move back to the start of our chunk
                ib.seek(-min(len(chunk), chunk_size), 1)
                prev_data = ib.read(chunk.index(boundary))[:-2]

                if prev_data:
                    if uploaded_file:
                        uploaded_file.file.write(prev_data)
                    elif name:
                        post_value += prev_data

                if uploaded_file:
                    uploaded_file.file.seek(0)
                    files.append(uploaded_file)
                    uploaded_file = None
                elif post_value:
                    post.add(name, post_value)
                    post_value = ''

                name, filename, mime_type = None, None, None

                while True:
                    header = ib.readline().strip()
                    if not header:
                        # End of headers for this multipart.
                        break
                    m = re.match(r'Content\-Disposition: form\-data; name="([^"]+)"(?:; filename="([^"]+)")?$', header)
                    if m:
                        name, filename = m.groups()
                    m = re.match(r'Content-Type: (.+)$', header)
                    if m:
                        mime_type = m.group(1)

                if name and filename and mime_type:
                    # Create new uploaded file
                    uploaded_file = UploadedFile(name=name, filename=filename,
                                                 mime_type=mime_type)
                elif name:
                    post_value = ''

            elif uploaded_file or name:
                # Write chunk to uploaded_file, minus len(boundary)
                if len(chunk) == chunk_size:
                    end = -len(boundary)
                else:
                    end = len(chunk)
                if not chunk[:end]:
                    break
                if uploaded_file:
                    uploaded_file.file.write(chunk[:end])
                else:
                    post_value += chunk[:end]
                # Seek back
                ib.seek(end, 1)

            else:
                # Before the first boundary is an area that is
                # ignored by MIME-compliant clients. This area is
                # generally used to put a message to users of old
                # non-MIME clients.
                pass

        return post, files
