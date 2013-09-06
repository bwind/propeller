from propeller import Request
from propeller.uploaded_file import UploadedFile
from propeller.multipart import MultiPartParser


def setup():
    pass

def teardown():
    pass

def test_single_file():
    data = open('test/data/file.txt')
    req = Request()
    req._input = data
    req._parse()

    assert req.post == {}
    assert len(req.files) == 1
    assert isinstance(req.files[0], UploadedFile)
    assert len(req.files[0].file.read()) == 21743

def test_multiple_files():
    pass

def test_file_and_data():
    pass

def test_data():
    pass
