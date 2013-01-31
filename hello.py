from propeller import Application, RequestHandler, Response

class HomeHandler(RequestHandler):
    def get(self, request):
        return Response('Hello, World!')

a = Application([
    (r'^/', HomeHandler),
])

if __name__ == '__main__':
    a.run()
