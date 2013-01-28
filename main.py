from propeller.app import Application
from handlers.home import HomeHandler

urls = (
    (r'^/home/([0-9]+)$', HomeHandler, {'lala': 'foo'}),
)

settings = {'urls': urls, 'debug': True}

a = Application(**settings)
a.run()
