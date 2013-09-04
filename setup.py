from setuptools import setup


setup(
    name='Propeller',
    version='0.1.6',
    author='Bas Wind',
    author_email='mailtobwind@gmail.com',
    packages=['propeller'],
    include_package_data=True,
    scripts=[],
    url='http://www.propellerframework.org/',
    download_url='https://pypi.python.org/pypi/Propeller',
    license='LICENSE.txt',
    description='A lightweight HTTP framework written in Python',
    long_description=open('README.txt').read(),
    keywords='web server http framework fast',
    install_requires=[
        'Jinja2==2.7.1',
    ],
)
