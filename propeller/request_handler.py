from propeller.response import Response, NotFoundResponse

import os
import mimetypes


class RequestHandler(object):
    def __handle(self, method):
        return Response('')

    def get(self, *args, **kwargs):
        return self.__handle('get')

    def post(self, *args, **kwargs):
        return self.__handle('post')

    def put(self, *args, **kwargs):
        return self.__handle('put')

    def delete(self, *args, **kwargs):
        return self.__handle('delete')

    def head(self, *args, **kwargs):
        return self.__handle('head')

    def options(self, *args, **kwargs):
        return self.__handle('options')


class StaticFileHandler(RequestHandler):
    def get(self, request, path, static_path):
        loc = os.path.join(static_path, path)
        if not loc.startswith(static_path) or not os.path.exists(loc):
            return NotFoundResponse()
        r = Response(open(loc).read())
        mime = mimetypes.guess_type(loc)
        if mime:
            hdr = '; '.join(mime) if mime[1] is not None else mime[0]
            r.headers['Content-Type'] = hdr
        return r
