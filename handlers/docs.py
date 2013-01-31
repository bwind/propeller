from propeller import RequestHandler, Response, Template


class DocsHandler(RequestHandler):
    def get(self, request):
        return Response(Template('docs.html'))
