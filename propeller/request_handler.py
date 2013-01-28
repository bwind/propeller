from propeller.response import Response


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
