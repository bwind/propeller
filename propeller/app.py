from jinja2 import Environment, FileSystemLoader, PackageLoader
from propeller.loop import Loop
from propeller.options import Options
from propeller.reloader import Reloader
from propeller.response import *
from propeller.request import Request
from propeller.request_handler import RequestHandler
from propeller.template import Template

import logging
import os
import propeller
import re
import socket
import sys
import time
import traceback
import Queue


bufsize = 4096


class Application(object):
    def __init__(self, urls=(), host='127.0.0.1', port=8080, debug=False,
                 tpl_dir='templates'):
        self.urls = urls
        self.host = host
        self.port = port
        self.urls = urls

        # Set application-wide options
        Options.debug = debug
        Options.tpl_env = Environment(loader=PackageLoader('propeller', \
            'templates'), autoescape=True)

        # Set the template dir
        self.tpl_dir = os.path.join(sys.path[0], tpl_dir)

        # Set up logging
        self.logger = logging.getLogger(__name__)
        level = logging.INFO if debug is False else logging.DEBUG
        self.logger.setLevel(level=level)
        ch = logging.StreamHandler()
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(message)s',
                                      '%Y-%m-%d %H:%M:%S')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

        # Template environment for internal templates
        Template.env = Environment(loader=FileSystemLoader(self.tpl_dir),
                                   autoescape=True)

    def run(self):
        if Options.debug:
            # Run Propeller with reloader
            Reloader.run_with_reloader(self, self._run)
        else:
            self._run()

    def _run(self):
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.setblocking(0)
        self._server.bind((self.host, self.port))
        self._server.listen(1000)

        self.logger.info('* Propeller %s listening on %s:%d' % \
            (propeller.__version__, self.host, self.port))

        # Create an event loop and register our server socket.
        self._loop = Loop()
        self._loop.register(self._server, Loop.READ)

        self._requests = {}

        handlers = {
            Loop.READ: self._read_handler,
            Loop.WRITE: self._write_handler,
            Loop.ERROR: self._error_handler,
        }

        while True:
            events = self._loop.poll()
            for sock, mode in events:
                try:
                    handlers[mode](sock)
                except KeyError as e:
                    self.logger.error(e)
                    handlers[Loop.ERROR](sock)

    def _read_handler(self, sock):
        if sock == self._server:
            # A readable socket server is available to
            # accept a connection.
            conn, addr = sock.accept()
            conn.setblocking(0)
            self._loop.register(conn, Loop.READ)
            self._requests[conn.fileno()] = Request(sock=conn, ip=addr[0])
        else:
            # A readable client socket has data.
            request = self._requests[sock.fileno()]
            try:
                data = sock.recv(bufsize)
                if data:
                    request._write(data)
            except socket.error as e:
                self.logger.debug(e)
                if e.args[0] == 35:
                    # EAGAIN or EWOULDBLOCK, try again later
                    return
                data = ''
            if not request._has_more_data():
                # We have received all data from the
                # client. Unregister interest for further
                # reading.
                self._loop.unregister(sock, Loop.READ)

                # Only process this request if we have data
                # in the input buffer.
                if request._input.tell() > 0:
                    response = ''
                    self._loop.register(sock, Loop.WRITE)

                    try:
                        request._parse()
                    except Exception as e:
                        # Any type of exception is considered
                        # as an invalid request and means we're
                        # returning a 400 Bad Request.
                        self.logger.error(e)
                        request = Request(ip=sock.getpeername()[0])
                        response = BadRequestResponse()
                    else:
                        # Delegate the request to a
                        # RequestHandler.
                        response = self._handle_request(request)

                        # Store the response in the output buffer so we
                        # can send it when there is a socket available
                        # for writing.
                        request._output.put(str(response))
                        self._log_request(request, response)

    def _write_handler(self, sock):
        # This socket is available for writing.
        try:
            output = self._requests[sock.fileno()]._output.get_nowait()
        except Queue.Empty:
            # We're done sending. Clean up.
            self._loop.unregister(sock, Loop.WRITE)
            self._loop.close_socket(sock)
        else:
            total_sent = 0
            while total_sent < len(output):
                try:
                    sent = sock.send(output[total_sent:])
                except socket.error as e:
                    sent = 0
                total_sent = total_sent + sent

    def _error_handler(self, sock):
        # Stop listening for all events and close the
        # socket.
        self._loop.unregister(sock, Loop.READ)
        self._loop.unregister(sock, Loop.WRITE)
        self._loop.close_socket(sock)

    def _handle_request(self, request):
        # Iterates over self.urls to match the requested URL and stops
        # after the first match.
        handler = None
        for url in self.urls:
            match = re.match(url[0], request.url)
            if match:
                handler = url[1]()
                break
        if not handler:
            # Request URL did not match any of the urls. Return a
            # NotFoundResponse.
            return NotFoundResponse(request.url)
        else:
            method = request.method.lower()
            args = match.groups() if match else ()
            kwargs = url[2] if len(url) > 2 else {}

            body = ''
            if request.method not in RequestHandler.supported_methods or \
                not hasattr(handler, method):
                # The HTTP method was not defined in the handler.
                # Return a 404.
                return NotFoundResponse(request.url)
            else:
                request._start_time = time.time()
                try:
                    response = getattr(handler, method)(request,
                                                        *args,
                                                        **kwargs)
                    assert isinstance(response, Response), \
                        'RequestHandler did not return instance of Response'
                    return response
                except Exception as e:
                    # Handle uncaught exception from the
                    # RequestHandler.
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

    def _log_request(self, request, response):
        ms = '%0.2fms' % round(request._execution_time * 1000, 2)
        method = request.method if request.method in \
            RequestHandler.supported_methods else '-'
        log = ' '.join([
            str(response.status_code),
            method,
            request.path,
            str(len(response.body)),
            ms,
            '(%s)' % request.ip,
        ])
        self.logger.info(log)
