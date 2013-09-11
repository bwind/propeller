from propeller import Request
from propeller.request_handler import StaticFileHandler
from . import staticdir


def setup():
    pass

def teardown():
    pass

def test_static_file_handler():
    req = Request()
    handler = StaticFileHandler()
    response = handler.get(req, 'panda-baby.jpg', staticdir)
    assert response.headers['Content-Type'] == ['image/jpeg']
    s = str(response)
    image_data = s[s.index('\r\n\r\n') + 4:]
    assert len(image_data) == 21743

def test_static_file_handler_404():
    req = Request()
    handler = StaticFileHandler()
    response = handler.get(req, 'doesnotexist.jpg', staticdir)
    assert response.status_code == 404

def test_static_file_handler_directory():
    req = Request()
    handler = StaticFileHandler()
    response = handler.get(req, 'empty', staticdir)
    assert response.status_code == 404
