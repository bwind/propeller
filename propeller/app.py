from jinja2 import Environment, FileSystemLoader, PackageLoader
from propeller.loop import Loop
from propeller.options import Options
from propeller.reloader import Reloader
from propeller.response import *
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
    def __init__(self, urls=(), host='127.0.0.1', port=8080, debug=False,
                 tpl_dir='templates'):
        self.urls = urls
        self.host = host
        self.port = port
        self.urls = urls

        Options.debug = debug
        Options.tpl_env = Environment(loader=PackageLoader('propeller', \
            'templates'), autoescape=True)

        self.tpl_dir = tpl_dir
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO,
                            format='[%(asctime)s] %(message)s')

        Template.env = Environment(loader=FileSystemLoader(self.tpl_dir),
                                   autoescape=True)

    def run(self):
        if Options.debug:
            Reloader.run_with_reloader(self, self.__run)
        else:
            self.__run()

    def __run(self):
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
                            try:
                                request = Request(data=data, ip=addr[0])
                            except TypeError:
                                """Any type of exception is considered
                                as an invalid request and means we're
                                returning a 400 Bad Request.
                                """
                                request = Request(ip=addr[0])
                                response = BadRequestResponse()
                            else:
                                response = self.handle_request(request)

                            output_buffer[fd].put(str(response))

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

    def handle_request(self, request):
        """Iterates over self.urls to match the requested URL and stops
        after the first match.
        """
        handler = None
        for url in self.urls:
            match = re.match(url[0], request.url)
            if match:
                handler = url[1]()
                break
        if not handler:
            """Request URL did not match any of the urls. Invoke the
            base RequestHandler and return a 404.
            """
            return NotFoundResponse(request.url)
        else:
            method = request.method.lower()
            args = match.groups() if match else ()
            kwargs = url[2] if len(url) > 2 else {}

            body = ''
            if not hasattr(handler, method) or request.method not in \
                RequestHandler.supported_methods:
                """The HTTP method was not defined in the handler.
                Return a 404.
                """
                return NotFoundResponse(request)
            else:
                try:
                    response = getattr(handler, method)(request,
                                                        *args,
                                                        **kwargs)
                    assert isinstance(response, Response), \
                        'RequestHandler did not return instance of Response'
                    return response
                except Exception, e:
                    """Handle uncaught exception from the
                    RequestHandler.
                    """
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    tb = ''.join([t for t \
                        in traceback.format_tb(exc_tb, limit=11)[1:]])
                    fname, lineno, func, err = \
                        traceback.extract_tb(exc_tb)[-1]

                    title = '%s: %s' % (exc_type.__name__, e)
                    subtitle = '%s, line %d' % (fname, lineno)

                    message = '%s: %s\n%s' % (exc_type.__name__, e, tb)
                    self.logger.error(message.strip())

                    return InternalServerErrorResponse(title, subtitle, tb)

    def log_request(self, request, response):
        ms = '%0.2fms' % round(request.execution_time * 1000, 2)
        method = request.method if request.method in \
            RequestHandler.supported_methods else '-'
        log = ' '.join([
            str(response.status_code),
            method,
            request.url,
            str(len(response.body)),
            ms,
            '(%s)' % request.ip
        ])
        self.logger.info(log)
