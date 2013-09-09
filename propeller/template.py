from jinja2 import Environment, PackageLoader


class Template(object):
    env = None
    def __init__(self, template, tpl_vars={}):
        self._template = template
        self._tpl_vars = tpl_vars
        self._compiled = None

    def __str__(self):
        if not self._compiled:
            t = self.env.get_template(self._template)
            self._compiled = t.render(**self._tpl_vars)
        return self._compiled.encode('utf-8')
