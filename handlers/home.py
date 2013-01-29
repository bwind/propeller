from propeller import RequestHandler, Response, Template


class HomeHandler(RequestHandler):
    def get(self, request, test):
        tpl_vars = {'content': 'foo'}
        return Response(Template('layout.html', tpl_vars))
