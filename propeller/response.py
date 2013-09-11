from datetime import timedelta
from propeller.cookie import Cookie
from propeller.options import Options
from propeller.template import Template
from propeller.util.dict import MultiDict
from urllib import quote

import httplib
import propeller


class Response(object):
    def __init__(self, body='', status_code=200, content_type='text/html'):
        self.body = body
        self.status_code = status_code
        self.headers = MultiDict()
        self.cookies = []
        self.headers['Content-Type'] = content_type

    def _get_status_code(self):
        return self._status_code

    def _set_status_code(self, status_code):
        assert status_code >= 200 and status_code <= 500, \
            'status_code must be an int between 200 and 500'
        self._status_code = status_code

    def _get_body(self):
        return self._body

    def _set_body(self, body):
        assert isinstance(body, basestring) or isinstance(body, Template), \
            'body must be an instance of basestring or Template'
        if isinstance(body, basestring):
            self._body = body
        elif isinstance(body, Template):
            self._body = str(body)

    def _build_headers(self):
        self.headers['Content-Length'] = len(self.body)
        if 'Content-Type' not in self.headers or not \
            self.headers['Content-Type'][0]:
            self.headers['Content-Type'] = 'text/html; charset=utf-8'
        status = 'HTTP/1.0 %d %s' % (self.status_code,
                                     httplib.responses[self.status_code])

        headers = ['%s: %s' % (k, v) for k, v in self.headers.items()]
        headers += ['Set-Cookie: %s' % str(c) for c in self.cookies]
        headers = '\r\n'.join([status] + headers) + '\r\n\r\n'
        return headers

    def _error_page(self, title, subtitle='', traceback=None):
        t = Options.tpl_env.get_template('error.html')
        return t.render(
            title=title,
            subtitle=subtitle,
            traceback=traceback,
            version=propeller.__version__
        )

    def set_cookie(self, name, value, domain=None, expires=None, path=None,
                   secure=False):
        self.cookies.append(Cookie(name=name, value=value, domain=domain,
                                   expires=expires, path=path, secure=secure))

    def __str__(self):
        return self._build_headers() + self.body

    status_code = property(_get_status_code, _set_status_code)
    body = property(_get_body, _set_body)


class RedirectResponse(Response):
    def __init__(self, redirect_url, permanent=False, *args, **kwargs):
        status_code = 301 if permanent else 302
        super(RedirectResponse, self).__init__(status_code=status_code, *args,
                                               **kwargs)
        self.redirect_url = redirect_url

    def __str__(self):
        if 'Location' not in self.headers:
            self.headers['Location'] = self.redirect_url
        return super(RedirectResponse, self).__str__()


class BadRequestResponse(Response):
    def __init__(self, *args, **kwargs):
        super(BadRequestResponse, self).__init__(status_code=400, *args,
                                                 **kwargs)

    def __str__(self):
        if not self.body and Options.debug:
            self.body = self._error_page(httplib.responses[self.status_code])
        return super(BadRequestResponse, self).__str__()


class NotFoundResponse(Response):
    def __init__(self, url=None, *args, **kwargs):
        super(NotFoundResponse, self).__init__(status_code=404, *args,
                                               **kwargs)
        self.url = url

    def __str__(self):
        if not self.body and Options.debug:
            self.body = self._error_page(httplib.responses[self.status_code],
                                         self.url)
        return super(NotFoundResponse, self).__str__()


class InternalServerErrorResponse(Response):
    def __init__(self, title, subtitle, traceback, *args, **kwargs):
        super(InternalServerErrorResponse, self).__init__(status_code=500,
                                                          *args, **kwargs)
        self.title = title
        self.subtitle = subtitle
        self.traceback = traceback

    def __str__(self):
        if not self.body and Options.debug:
            self.body = self._error_page(self.title,
                                         self.subtitle,
                                         self.traceback)
        return super(InternalServerErrorResponse, self).__str__()

