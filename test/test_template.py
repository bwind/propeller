from datetime import datetime, timedelta
from jinja2 import FileSystemLoader, Environment
from propeller import Template
from . import templatedir


def setup():
    pass

def teardown():
    pass

def test_template():
    Template.env = Environment(loader=FileSystemLoader(templatedir),
                               autoescape=True)
    t = Template('template.html', {'foo': 'bar'})
    assert str(t) == '<b>bar</b>'
    # And again, to test the cached version
    assert str(t) == '<b>bar</b>'
