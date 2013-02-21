from setuptools import setup

setup(
    name='Propeller',
    version='0.1.2',
    author='Bas Wind',
    author_email='mailtobwind@gmail.com',
    packages=['propeller'],
    include_package_data=True,
    scripts=[],
    url='http://pypi.python.org/pypi/Propeller/',
    license='LICENSE.txt',
    description='A lightweight HTTP framework written in Python',
    long_description=open('README.txt').read(),
    install_requires=[
        'Jinja2==2.6',
    ],
)
