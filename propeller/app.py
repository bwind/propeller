from jinja2 import Environment, FileSystemLoader, PackageLoader
from propeller.loop import Loop
from propeller.reloader import Reloader
from propeller.response import Response
from propeller.request import Request
from propeller.request_handler import RequestHandler
from propeller.template import Template

import httplib
import logging
import os
import propeller
import re
import select
import socket
import sys
import time
import traceback
import Queue


class Application(object):
    def __init__(self, host='127.0.0.1', port=8080, urls=(), debug=False,
                 tpl_dir='templates'):
        self.host = host
        self.port = port
        self.urls = urls
        self.debug = debug
        self.tpl_dir = tpl_dir

        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO,
                            format='[%(asctime)s] %(message)s')

        Template.env = Environment(loader=FileSystemLoader(self.tpl_dir),
                                   autoescape=True)

    def run(self):
        if self.debug:
            Reloader.run_with_reloader(self, self.__run)
        else:
            self.__run()

    def __run(self):
        self.tpl_env = Environment(loader=PackageLoader('propeller', \
            'templates'), autoescape=True)

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.setblocking(0)
        server.bind((self.host, self.port))
        server.listen(1000)

        self.logger.info('* Propeller %s Listening on %s:%d' % \
            (propeller.__version__, self.host, self.port))

        self.loop = Loop()
        self.loop.register(server, Loop.READ)

        output_buffer = {}

        while True:

            events = self.loop.poll()

            for sock, mode in events:
                fd = sock.fileno()

                if mode & Loop.READ:
                    if sock == server:
                        """A readable socket server is available to accept
                        a connection.
                        """
                        conn, addr = server.accept()
                        conn.setblocking(0)
                        self.loop.register(conn, Loop.READ)

                        output_buffer[conn.fileno()] = Queue.Queue()
                    else:
                        try:
                            data = sock.recv(1024)
                        except socket.error:
                            continue
                        if data:
                            """A readable client socket has data.
                            """
                            request = Request(data)
                            request.ip = addr[0]
                            response = self.handle_request(request)

                            message = self.get_response_headers(response)
                            message += response.body
                            output_buffer[fd].put(message)

                            self.loop.register(sock, Loop.WRITE)
                            self.log_request(request, response)
                        else:
                            """Interpret empty result as an EOF from
                            the client.
                            """
                            self.loop.unregister(sock, Loop.READ)
                            self.loop.unregister(sock, Loop.WRITE)
                            self.loop.close_socket(sock)
                            try:
                                del output_buffer[fd]
                            except:
                                pass
                # Handle outputs
                elif mode & Loop.WRITE:
                    """This socket is available for writing.
                    """
                    try:
                        next_msg = output_buffer[fd].get_nowait()
                    except Queue.Empty:
                        self.loop.unregister(sock, Loop.WRITE)
                    else:
                        sock.send(next_msg)
                # Handle "exceptional conditions"
                elif mode & Loop.ERROR:
                    self.logger.error('Exception on', sock.fileno())
                    # Stop listening for input on the connection
                    self.loop.unregister(sock, Loop.READ)
                    self.loop.unregister(sock, Loop.WRITE)
                    self.loop.close_socket(sock)
                    try:
                        del output_buffer[fd]
                    except:
                        pass

    def get_response_headers(self, response):
        response.headers['Content-Length'] = len(response.body)
        if 'Content-Type' not in response.headers:
            response.headers['Content-Type'] = 'text/html; charset=utf-8'

        status = 'HTTP/1.1 %d %s' % (response.status_code,
                                     httplib.responses[response.status_code])
        return '\r\n'.join([status] + ['%s: %s' % (k, v) for k, v \
            in response.headers.items()]) + '\r\n\r\n'

    def handle_request(self, request):
        """Figure out which RequestHandler to invoke.
        """
        handler = None
        response = Response()
        for u in self.urls:
            m = re.match(u[0], request.url)
            if m:
                handler = u[1]()
                break
        if not handler:
            """Request URL did not match any of the urls. Invoke the
            base RequestHandler and return a 404.
            """
            handler = RequestHandler()
            response.status_code = 404

            if self.debug:
                t = self.tpl_env.get_template('error.html')
                response.body = t.render(
                    title='Not found',
                    subtitle=request.url,
                    traceback=None,
                    version=propeller.__version__
                )
        else:
            method = request.method.lower()
            args = m.groups() if m else ()
            kwargs = u[2] if len(u) > 2 else {}

            body = ''
            if not hasattr(handler, method):
                """The HTTP method was not defined in the handler.
                Return a 404.
                """
                response.status_code = 404
            else:
                try:
                    res = getattr(handler, method)(request, *args, **kwargs)
                    assert isinstance(res, Response) is True, \
                        'RequestHandler did not return instance of Response'
                    response = res
                except Exception, e:
                    """Handle uncaught exception from the
                    RequestHandler.
                    """
                    response.status_code = 500

                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    tb = ''.join([t for t \
                        in traceback.format_tb(exc_tb, limit=11)[1:]])
                    fname, lineno, func, err = \
                        traceback.extract_tb(exc_tb)[-1]

                    if not self.debug:
                        response.body = ''
                    else:
                        t = self.tpl_env.get_template('error.html')
                        response.body = t.render(
                            title='%s: %s' % (exc_type.__name__, e),
                            subtitle='%s, line %d' % (fname, lineno),
                            traceback=tb,
                            version=propeller.__version__
                        )

                    self.logger.error('%s: %s\n%s' % (exc_type.__name__, e,
                                                      tb.strip()))

        return response

    def log_request(self, request, response):
        ms = '%0.2fms' % round(request.execution_time * 1000, 2)
        log = ' '.join([
            str(response.status_code),
            request.method,
            request.url,
            str(len(response.body)),
            ms,
            '(%s)' % request.ip
        ])
        self.logger.info(log)
