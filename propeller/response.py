from propeller.util.multidict import MultiDict


class Response(object):
    def __init__(self):
        self.__status_code = 200
        self.headers = MultiDict()
        self.body = ''

    def set_status_code(self, status_code):
        assert status_code >= 200 and status_code <= 500
        self.__status_code = status_code

    @property
    def status_code(self):
        return self.__status_code