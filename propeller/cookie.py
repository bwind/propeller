from datetime import datetime
from datetime import timedelta
from urllib import quote


class Cookie(object):
    def __init__(self, name, value, domain=None, expires=None, path=None,
                 secure=False):
        self.name = name
        self.value = value
        self.domain = domain
        self.expires = expires
        self.path = path
        self.secure = secure

    def __str__(self):
        val = '%s=%s' % (
            self.name,
            quote(self.value)
        )
        if self.domain:
            val += '; domain=%s' % self.domain
        if self.path:
            val += '; path=%s' % self.path
        if self.expires:
            expires = datetime.now() + self.expires
            val += '; expires=%s GMT' % \
                expires.strftime('%a %d %b %Y %H:%M:%S')
        if self.secure:
            val += '; secure'
        return val
