from propeller import RequestHandler, Response, Template


class HomeHandler(RequestHandler):
    def get(self, request, test):
        tpl_vars = {'content': '<h1>Propeller HTTP Framework</h1><p>Foo.</p>'}
        return Response(Template('layout.html', tpl_vars))
