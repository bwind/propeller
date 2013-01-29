from jinja2 import Environment, PackageLoader


class Template(object):
    env = None
    def __init__(self, template, tpl_vars):
        self.__template = template
        self.__tpl_vars = tpl_vars
        self.__compiled = None

    def __str__(self):
        if not self.__compiled:
            t = self.env.get_template(self.__template)
            self.__compiled = t.render(**self.__tpl_vars)
        return self.__compiled
