from propeller import Request
from propeller.uploaded_file import UploadedFile
from . import requestdir


def setup():
    pass

def teardown():
    pass

def test_single_file():
    req = Request()
    req._input = open('%s/file.txt' % requestdir)
    req._parse()

    assert req.post == {}
    assert len(req.files) == 1
    assert isinstance(req.files[0], UploadedFile)
    assert len(req.files[0].file.read()) == 21743

def test_multiple_files():
    req = Request()
    req._input = open('%s/files.txt' % requestdir)
    req._parse()

    assert len(req.post) == 0
    assert len(req.files) == 2

    assert isinstance(req.files[0], UploadedFile)
    assert len(req.files[0].file.read()) == 21743
    assert req.files[0].filename == 'panda-baby.jpg'

    assert isinstance(req.files[1], UploadedFile)
    assert len(req.files[1].file.read()) == 16970
    assert req.files[1].filename == 'puppy-small.jpg'

def test_file_and_data():
    req = Request()
    req._input = open('%s/mixed.txt' % requestdir)
    req._parse()

    assert len(req.post) == 1
    assert len(req.files) == 1

    assert req.post['text1'][0] == 'asdf'

    assert isinstance(req.files[0], UploadedFile)
    assert len(req.files[0].file.read()) == 21743
    assert req.files[0].filename == 'panda-baby.jpg'

def test_data():
    req = Request()
    req._input = open('%s/data.txt' % requestdir)
    req._parse()

    expected = {
        'text1': 'foo',
        'text2': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc porta tempus venenatis. Proin lobortis tempor ante, id ornare nisl dignissim vitae. Nullam in placerat metus.\r\n\r\nDonec nisi nisi, ultricies cursus enim ac, tempor sodales sem. Sed sit amet fermentum nisi, id fringilla libero. Praesent eget ante lacus. Nunc pretium velit est, sed lacinia eros lacinia a. Donec in neque tempus, vehicula odio ac, condimentum mi. Nulla id tristique nisi, ac consequat eros.'}

    assert len(req.post) == 2
    for key in expected:
        assert req.post[key][0] == expected[key]
