from propeller import RequestHandler


class HomeHandler(RequestHandler):
    def get(self, test):
        self.response.body = 'hello3' + test
