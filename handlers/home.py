from propeller import RequestHandler, Response


class HomeHandler(RequestHandler):
    def get(self, request, test):
        return Response('hoi, jij bent<html>\'\'... %s' % request.headers['User-Agent'][0])
