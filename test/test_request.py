from propeller import Request
from . import requestdir


def setup():
    pass

def teardown():
    pass

def test_message_bytes():
    req = Request()
    req._write(open('%s/mixed.txt' % requestdir).read())
    req._parse()

    assert req._message_bytes == 22028

def test_get_message_start():
    req = Request()
    req._write(open('%s/mixed.txt' % requestdir).read())
    req._parse()

    assert req._get_message_start() == 487

def test_headers():
    req = Request()
    req._write(open('%s/mixed.txt' % requestdir).read())
    req._parse()

    headers = {
        'Host': 'localhost:9999',
        'Connection': 'keep-alive',
        'Content-Length': '22028',
        'Cache-Control': 'max-age=0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Origin': 'null',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.62 Safari/537.36',
        'Content-Type': 'multipart/form-data; boundary=----WebKitFormBoundarygQtUpZGpES2gHbcb',
        'Accept-Encoding': 'gzip,deflate,sdch',
        'Accept-Language': 'en-US,en;q=0.8',
    }

    for k, v in headers.items():
        assert req.headers[k] == [v]

def test_invalid_header():
    req = Request()
    req._write(open('%s/invalid_header.txt' % requestdir).read())
    req._parse()

    assert len(req.headers) == 1
    assert req.headers['Host'] == ['localhost:9999']

def test_get_params():
    req = Request()
    req._write(open('%s/get_params.txt' % requestdir).read())
    req._parse()

    assert len(req.get) == 2
    assert req.get['test'] == ['hello']
    assert req.get['foo'] == ['bar']

def test_execution_time():
    req = Request()
    req._write(open('%s/get_params.txt' % requestdir).read())
    req._parse()

    assert req._execution_time >= 0

def test_has_more_data():
    req = Request()

    with open('%s/mixed.txt' % requestdir) as f:
        # First only write headers to request
        while True:
            line = f.readline()
            req._write(line)
            if not line.strip():
                break

        # Headers contain content-length, so there must be more data
        assert req._has_more_data() == True

        # Write rest of request
        data = f.read()
        req._write(data)

        assert req._has_more_data() == False

def test_cookies():
    req = Request()

    with open('%s/cookie.txt' % requestdir) as f:
        req._write(f.read())
        req._parse()

        assert len(req.cookies) == 2
        assert req.cookies[0].name == 'name'
        assert req.cookies[0].value == 'value'
        assert req.cookies[1].name == 'name2'
        assert req.cookies[1].value == 'value2'

def test_x_real_ip():
    req = Request()
    with open('%s/x_real_ip.txt' % requestdir) as f:
        req._write(f.read())
        req._parse()
        assert req.ip == '9.9.9.9'

def test_x_forwarded_for():
    req = Request()
    with open('%s/x_forwarded_for.txt' % requestdir) as f:
        req._write(f.read())
        req._parse()
        assert req.ip == '9.9.9.9'
