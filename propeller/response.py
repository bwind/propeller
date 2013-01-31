from propeller.options import Options
from propeller.template import Template
from propeller.util.dict import MultiDict

import httplib
import propeller


class Response(object):
    __body = ''
    __status_code = 200
    headers = MultiDict()

    def __init__(self, body='', status_code=200,
                 content_type='text/html; charset=utf-8'):
        self.body = body
        self.status_code = status_code
        self.headers = MultiDict()
        self.headers['Content-Type'] = content_type

    def __get_status_code(self):
        return self.__status_code

    def __set_status_code(self, status_code):
        assert status_code >= 200 and status_code <= 500, \
            'status_code must be an int between 200 and 500'
        self.__status_code = status_code

    def __get_body(self):
        return self.__body

    def __set_body(self, body):
        assert isinstance(body, basestring) or isinstance(body, Template), \
            'body must be an instance of basestring or Template'
        if isinstance(body, basestring):
            self.__body = body
        elif isinstance(body, Template):
            self.__body = str(body)

    def _build_headers(self):
        self.headers['Content-Length'] = len(self.body)
        if 'Content-Type' not in self.headers:
            self.headers['Content-Type'] = 'text/html; charset=utf-8'
        status = 'HTTP/1.1 %d %s' % (self.status_code,
                                     httplib.responses[self.status_code])
        headers = '\r\n'.join([status] + ['%s: %s' % (k, v) for k, v \
            in self.headers.items()]) + '\r\n\r\n'
        return headers

    def _error_page(self, title, subtitle='', traceback=None):
        t = Options.tpl_env.get_template('error.html')
        return t.render(
            title=title,
            subtitle=subtitle,
            traceback=traceback,
            version=propeller.__version__
        )

    def __str__(self):
        return self._build_headers() + self.body

    status_code = property(__get_status_code, __set_status_code)
    body = property(__get_body, __set_body)


class BadRequestResponse(Response):
    def __init__(self):
        super(BadRequestResponse, self).__init__(status_code=400)

    def __str__(self):
        if not self.body and Options.debug:
            self.body = self._error_page('Bad Request')
        return self._build_headers() + self.body


class NotFoundResponse(Response):
    def __init__(self, request, *args, **kwargs):
        super(NotFoundResponse, self).__init__(status_code=404)
        self.request = request

    def __str__(self):
        if not self.body and Options.debug:
            self.body = self._error_page('Not Found', self.request.url)
        return self._build_headers() + self.body


class InternalServerErrorResponse(Response):
    def __init__(self, request, title, subtitle, traceback, *args, **kwargs):
        super(InternalServerErrorResponse, self).__init__(status_code=500)
        self.request = request
        self.title = title
        self.subtitle = subtitle
        self.traceback = traceback

    def __str__(self):
        if not self.body and Options.debug:
            self.body = self._error_page(self.title,
                                         self.subtitle,
                                         self.traceback)
        return self._build_headers() + self.body

