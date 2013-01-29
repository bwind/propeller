from propeller.app import Application
from propeller.request_handler import StaticFileHandler
from handlers.home import HomeHandler

urls = (
    (r'^/home/([0-9]+)$', HomeHandler),
    (r'^/static/(.*)$', StaticFileHandler, {'static_path': '/Users/baswind/Projects/propeller-dev/static'}),
)

settings = {'urls': urls, 'debug': True}

a = Application(**settings)
a.run()
