from jinja2 import FileSystemLoader, Environment
from propeller import Options, Template
from propeller.response import *
from . import templatedir


Template.env = Environment(loader=FileSystemLoader(templatedir),
                           autoescape=True)
Options.debug = False


def test_default_content_type():
    res = Response(content_type='')
    assert 'Content-Type: text/html; charset=utf-8' in str(res)

def test_template():
    t = Template('template.html', {'foo': 'bar'})
    res = Response(t)
    assert '<b>bar</b>' in str(res)

def test_redirect_permanent():
    res = RedirectResponse('/some-url', permanent=True)
    assert res.status_code == 301
    assert 'Location: /some-url' in str(res)
    assert str(res).startswith('HTTP/1.0 301 Moved Permanently')

def test_redirect():
    res = RedirectResponse('/some-url')
    assert res.status_code == 302
    assert 'Location: /some-url' in str(res)
    assert str(res).startswith('HTTP/1.0 302 Found')

def test_bad_request():
    res = BadRequestResponse()
    assert res.status_code == 400
    assert str(res).startswith('HTTP/1.0 400 Bad Request')

def test_not_found_response():
    res = NotFoundResponse()
    assert res.status_code == 404
    assert str(res).startswith('HTTP/1.0 404 Not Found')

def test_internal_server_error():
    res = InternalServerErrorResponse('title', 'subtitle', [])
    assert res.status_code == 500
    assert str(res).startswith('HTTP/1.0 500 Internal Server Error')
