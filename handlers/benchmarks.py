from propeller import RequestHandler, Response, Template


class BenchmarksHandler(RequestHandler):
    def get(self, request):
        return Response(Template('benchmarks.html'))
