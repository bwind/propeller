from propeller.response import Response


class RequestHandler(object):
    def __init__(self, request):
        self.request = request
        self.response = Response()

    def __handle(self, method):
        return ''

    def get(self):
        return self.__handle('get')

    def post(self):
        return self.__handle('post')

    def put(self):
        return self.__handle('put')

    def delete(self):
        return self.__handle('delete')
