from propeller import RequestHandler, Response, Template


class DownloadsHandler(RequestHandler):
    def get(self, request):
        return Response(Template('downloads.html'))
