from propeller.response import Response, NotFoundResponse

import os
import mimetypes


class RequestHandler(object):
    supported_methods = ('GET', 'PUT', 'POST', 'DELETE', 'OPTIONS', 'HEAD')


class StaticFileHandler(RequestHandler):
    def get(self, request, path, static_path):
        loc = os.path.join(static_path, path)
        if not loc.startswith(static_path) or not os.path.isfile(loc):
            return NotFoundResponse()
        r = Response(open(loc).read())
        mime = mimetypes.guess_type(loc)
        if mime:
            hdr = '; '.join(mime) if mime[1] is not None else mime[0]
            r.headers['Content-Type'] = hdr
        return r
