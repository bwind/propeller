from propeller import RequestHandler


class HomeHandler(RequestHandler):
    def get(self, test, **kwargs):
        self.response.body = 'hoi, jij bent %s' % self.request.headers['User-Agent']
