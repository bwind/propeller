from jinja2 import Environment, PackageLoader
from propeller.loop import Loop
from propeller.reloader import Reloader
from propeller.response import Response
from propeller.request import Request
from propeller.request_handler import RequestHandler

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
    def __init__(self, host='localhost', port=8080, urls=(), debug=False):
        self.host = host
        self.port = port
        self.urls = urls
        self.debug = debug

        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

        self.tpl_env = Environment(loader=PackageLoader('propeller', 'templates'))

    def run(self):
        if self.debug:
            Reloader.run_with_reloader(self, self.__run)
        else:
            self.__run()

    def __run(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.setblocking(0)
        server.bind((self.host, self.port))
        self.logger.info('* Running on %s:%d' % (self.host, self.port))
        server.listen(1000)

        self.loop = Loop()
        self.loop.register(server, Loop.READ)

        self.message_queues = {}

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

                        self.message_queues[conn.fileno()] = Queue.Queue()
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
                            handler = self.handle_request(request)

                            message = \
                                self.get_response_headers(handler.response)
                            message += handler.response.body
                            self.message_queues[fd].put(message)

                            self.loop.register(sock, Loop.WRITE)
                            self.log_request(request, handler.response)

                        else:
                            """Interpret empty result as an EOF from
                            the client.
                            """
                            self.loop.unregister(sock, Loop.READ)
                            self.loop.unregister(sock, Loop.WRITE)
                            self.loop.close_socket(sock)
                            try:
                                del self.message_queues[fd]
                            except:
                                pass

                # Handle outputs
                elif mode & Loop.WRITE:
                    """This socket is available for writing.
                    """
                    try:
                        next_msg = self.message_queues[fd].get_nowait()
                    except Queue.Empty:
                        self.loop.unregister(sock, Loop.WRITE)
                    else:
                        sock.send(next_msg)

                # Handle "exceptional conditions"
                elif mode & Loop.ERROR:
                    print 'handling exceptional condition for', \
                        sock.fileno()
                    # Stop listening for input on the connection
                    self.loop.unregister(sock, Loop.READ)
                    self.loop.unregister(sock, Loop.WRITE)
                    self.loop.close_socket(sock)
                    try:
                        del self.message_queues[fd]
                    except:
                        pass


    def get_response_headers(self, response):
        response.headers['Content-Length'] = len(response.body)
        response.headers['Content-Type'] = 'text/html; charset=utf-8'

        status = 'HTTP/1.1 %d %s' % (response.status_code,
                                     httplib.responses[response.status_code])
        return '\r\n'.join([status] + ['%s: %s' % (k, v) for k, v \
            in response.headers.items()]) + '\r\n\r\n'

    def handle_request(self, request):
        """Figure out which RequestHandler to invoke.
        """
        handler = None
        for u in self.urls:
            m = re.match(u[0], request.url)
            if m:
                handler = u[1](request)
        if not handler:
            handler = RequestHandler(request)
            handler.response.set_status_code(404)

            t = self.tpl_env.get_template('error.html')
            handler.response.body = t.render(**{
                'title': 'Not found',
                'subtitle': request.url,
                'traceback': None,
                'version': propeller.__version__
            })
        else:
            method = request.method.lower()
            args = m.groups() if m else ()
            kwargs = u[2] if len(u) > 2 else {}

            body = ''
            if not hasattr(handler, method):
                handler.response.set_status_code(404)
            else:
                try:
                    getattr(handler, method)(*args, **kwargs)
                except Exception, e:
                    handler.response.set_status_code(500)

                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    tb = ''.join([t for t \
                        in traceback.format_tb(exc_tb, limit=11)[1:]])
                    fname, lineno, func, err = \
                        traceback.extract_tb(exc_tb)[-1]

                    if not self.debug:
                        handler.response.body = ''
                    else:
                        t = self.tpl_env.get_template('error.html')
                        handler.response.body = t.render(**{
                            'title': '%s: %s' % (exc_type.__name__, e),
                            'subtitle': '%s, line %d' % (fname, lineno),
                            'traceback': tb,
                            'version': propeller.__version__
                        })

                    self.logger.error('%s: %s\n%s' % (exc_type.__name__, e,
                                                      tb.strip()))

        return handler

    def log_request(self, request, response):
        ms = '%0.2fms' % round(request.execution_time * 1000, 2)
        log = ' '.join([
            str(response.status_code),
            request.method,
            str(len(response.body)),
            request.url,
            ms,
            '(%s)' % request.ip
        ])
        self.logger.info(log)
