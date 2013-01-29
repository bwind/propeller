from propeller.template import Template
from propeller.util.multidict import MultiDict


class Response(object):
    __body = ''
    __status_code = 200
    headers = MultiDict()

    def __init__(self, body=''):
        if isinstance(body, str):
            self.__body = body
        elif isinstance(body, Template):
            self.__body = str(body)
        self.headers = MultiDict()

    def __get_status_code(self):
        return self.__status_code

    def __set_status_code(self, status_code):
        assert status_code >= 200 and status_code <= 500, \
            'status_code must be an int between 200 and 500'
        self.__status_code = status_code

    def __get_body(self):
        return self.__body

    def __set_body(self, body):
        self.__body = body

    status_code = property(__get_status_code, __set_status_code)
    body = property(__get_body, __set_body)


class NotFoundResponse(Response):
    def __init__(self, *args, **kwargs):
        super(Response, self).__init__(*args, **kwargs)
        self.status_code = 404
