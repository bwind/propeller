from datetime import datetime, timedelta
from propeller.cookie import Cookie


def setup():
    pass

def teardown():
    pass

def test_cookie():
    td = timedelta(days=35, hours=5)
    expires = (datetime.now() + td).strftime('%a %d %b %Y %H:%M:%S')
    c = Cookie('test', 'foo', '.example.com', td, '/', False)
    want = 'test=foo; domain=.example.com; path=/; expires=%s GMT' % expires
    assert str(c) == want

def test_cookie_secure():
    c = Cookie('test', 'foo', secure=True)
    assert str(c).endswith('; secure')
