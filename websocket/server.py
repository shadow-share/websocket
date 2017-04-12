#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#

# If the connection is happening on an HTTPS (HTTP-over-TLS) port,
# perform a TLS handshake over the connection.

#  The absence of such a field is equivalent to the null value
# (meaning that if the server does not wish to agree to one of
# the suggested subprotocols, it MUST NOT send back a
# |Sec-WebSocket-Protocol| header field in its response).
# The empty string is not the same as the null value for these
# purposes and is not a legal value for this field.

# Supporting Multiple Versions of WebSocket Protocol


# a client MUST mask all frames that it sends to the server.

# A client MUST close a connection if it detects a masked
# frame.

# A fragmented message consists of a single frame with the FIN bit
# clear and an opcode other than 0, followed by zero or more frames
# with the FIN bit clear and the opcode set to 0, and terminated by
# a single frame with the FIN bit set and an opcode of 0

# For a text message sent as three fragments, the first
# fragment would have an opcode of 0x1 and a FIN bit clear, the
# second fragment would have an opcode of 0x0 and a FIN bit clear,
# and the third fragment would have an opcode of 0x0 and a FIN bit
# that is set.
#

#
# First fragment
#
#     FIN = 0, opcode = 1     # opcode = 1(text frame)
#
#
# Second fragment
#
#     FIN = 0, opcode = 0     # opcode = 0(continuation frame)
#
#
# Third fragment
#
#     FIN = 1, opcode = 0     # opcode = 0(continuation frame)

# Message fragments MUST be delivered to the recipient in the order
# sent by the sender.

# The fragments of one message MUST NOT be interleaved between the
# fragments of another message unless an extension has been
# negotiated that can interpret the interleaving.

# An endpoint MUST be capable of handling control frames in the
# middle of a fragmented message.

# A sender MAY create fragments of any size for non-control
# messages.

# Clients and servers MUST support receiving both fragmented and
# unfragmented messages.

# An intermediary MUST NOT change the fragmentation of a message if
# any reserved bit values are used and the meaning of these values
# is not known to the intermediary.

# IMPLEMENTATION NOTE: In the absence of any extension, a receiver
# doesn't have to buffer the whole frame in order to process it.  For
# example, if a streaming API is used, a part of a frame can be
# delivered to the application.  However, note that this assumption
# might not hold true for all future WebSocket extensions.

#  Sending and Receiving Data

# The endpoint MUST ensure the WebSocket connection is in the OPEN
# state (cf. Sections 4.1 and 4.2.2.)  If at any point the state of
# the WebSocket connection changes, the endpoint MUST abort the
# following steps.
import os
import abc
import sys
import atexit
import signal
import socket
import inspect
import functools
import selectors
from collections import deque, OrderedDict
from websocket.utils import (
    exceptions, logger, ws_utils, generic
)
from websocket.ext import (
    handler, router, http_verifier
)
from websocket.net import (
    ws_frame, tcp_stream, http_message
)
from websocket.controller import (
    base_controller, plain_controller
)
from websocket.controller.base_controller import BaseController


__all__ = ['create_websocket_server']


class Daemon(object):

    def __init__(self, *, debug=False, pid_file: str=None,
                 stdin: str='/dev/null',
                 stdout: str='/dev/null',
                 stderr: str='/dev/null'):
        self._debug = debug
        self._stdin = stdin  # type: str
        self._stdout = stdout  # type: str
        self._stderr = stderr  # type: str
        if pid_file is None:
            pid_file = '/tmp/websocket_server.pid'
        self._pid_file = os.path.abspath(pid_file)  # type: str

    def run_forever(self):
        if self._debug:
            logger.warning('Debugger is active!')
            return

        if os.path.isfile(self._pid_file):
            raise exceptions.DeamonError(
                'pid file already exists, server running?')
        self._start_deamon()

    def _start_deamon(self):
        if not self._debug and (os.name == 'nt' or not hasattr(os, 'fork')):
            raise exceptions.DeamonError('Windows does not support fork')
        # double fork create a deamon
        try:
            pid = os.fork()  # fork #1
            if pid > 0:  # parent exit
                exit()
        except OSError as e:
            raise exceptions.FatalError(
                'Fork #1 error occurs, reason({})'.format(e))

        os.chdir('/')
        os.setsid()
        os.umask(0)

        try:
            pid = os.fork()  # fork #2
            if pid > 0:  # parent exit
                exit()
        except OSError as e:
            raise exceptions.FatalError(
                'Fork #2 error occurs, reason({})'.format(e))

        # redirect all std file descriptor
        sys.stdout.flush()
        sys.stderr.flush()
        _stdin = open(self._stdin, 'r')
        _stdout = open(self._stdout, 'a')
        # if require non-buffer, open mode muse be `b`
        _stderr = open(self._stderr, 'wb+', buffering=0)
        os.dup2(_stdin.fileno(), sys.stdin.fileno())
        os.dup2(_stdout.fileno(), sys.stdout.fileno())
        os.dup2(_stderr.fileno(), sys.stderr.fileno())

        # terminal signal
        signal.signal(signal.SIGTERM, self._signal_handler)
        # kill signal
        signal.signal(signal.SIGILL, self._signal_handler)
        # system interrupt
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        # register function at exit
        atexit.register(self._remove_pid_file)
        # write pid file
        with open(self._pid_file, 'w') as fd:
            fd.write('{pid}\n'.format(pid=os.getpid()))
        logger.info('Daemon has been started')

    def _signal_handler(self, signum, frame):
        logger.info('Daemon receive an exit signal({}: {})'.format(
            signum, frame))
        self._remove_pid_file()
        exit()

    def _remove_pid_file(self):
        logger.info('Daemon has exited')
        if os.path.exists(self._pid_file):
            os.remove(self._pid_file)


class WebSocketServerBase(Daemon, metaclass=abc.ABCMeta):

    # max message queue size
    LISTEN_SIZE = 16

    def __init__(self, host: str, port: int, *, pid_file=None, debug=False):
        """ WebSocketServerBase members

        :type self._server_fd: socket.socket
        :type self._client_list: dict[str, dict[socket.socket, BaseController]]
        :type self._server_address: tuple
        """
        super(WebSocketServerBase, self).__init__(pid_file=pid_file,
                                                  debug=debug)
        # server file descriptor
        self._server_fd = None
        # all handshake client
        self._client_list = {'default': {}}
        # Server address information
        self._server_address = (host, port)
        # Write queue
        self._write_queue = OrderedDict()
        # close frame information (endpoint, receive/send close flag)
        self._close_information = dict()
        # router object
        self._router = router.Router()
        # register default controller
        self.register_default_controller(plain_controller.PlainController)

    def register_handler(self, namespace):
        exceptions.raise_parameter_error('namespace', str, namespace)

        def _decorator_wrapper(class_object):
            if not issubclass(class_object, handler.WebSocketHandlerProtocol):
                raise exceptions.ParameterError(
                    'handlers must be derived with WebSocketHandlerProtocol')
            self._router.register(namespace, 'handler', class_object)
            class_object.__namespace__ = namespace
            logger.info("Handler: '{namespace}' => {handler}".format(
                namespace=namespace, handler=class_object))

            @functools.wraps(class_object)
            def _handler_wrapper(*args, **kwargs):
                return class_object(*args, **kwargs)
            return _handler_wrapper
        return _decorator_wrapper

    def register_default_handler(self, class_object):
        if not issubclass(class_object, handler.WebSocketHandlerProtocol):
            raise exceptions.ParameterError(
                'handlers must be derived with WebSocketHandlerProtocol')
        logger.info('Default handler: {}'.format(class_object))
        self._router.register_default('handler', class_object)

        @functools.wraps(class_object)
        def _handler_wrapper(*args, **kwargs):
            return class_object(*args, **kwargs)
        return _handler_wrapper

    def register_controller(self, namespace, controller_name):
        exceptions.raise_parameter_error('namespace', str, namespace)
        if not issubclass(controller_name, base_controller.BaseController):
            raise exceptions.ParameterError(
                'handlers must be derived with WebSocketHandlerProtocol')
        self._router.register(namespace, 'controller', controller_name)
        logger.info("Controller: {namespace} => {controller}".format(
            namespace=namespace, controller=controller_name))

    def register_default_controller(self, controller_name):
        if not issubclass(controller_name, base_controller.BaseController):
            raise exceptions.ParameterError(
                'handlers must be derived with WebSocketHandlerProtocol')
        logger.info('Default controller: {}'.format(controller_name))
        self._router.register_default('controller', controller_name)

    def run_forever(self):
        # Start deamon on background
        super(WebSocketServerBase, self).run_forever()
        # Create server socket file descriptor
        self._server_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Set socket option, REUSEADDR = True
        self._server_fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Set using non-block socket
        self._server_fd.setblocking(False)
        # Bind server listen port
        self._server_fd.bind(self._server_address)
        # Max connect queue size
        self._server_fd.listen(WebSocketServer.LISTEN_SIZE)
        logger.info('Server running in {}:{}'.format(*self._server_address))
        # enter the main loop
        self._select_loop()

    def _select_loop(self):
        self._selector = selectors.DefaultSelector()
        self._selector.register(
            self._server_fd, selectors.EVENT_READ, (self._accept_client, None))

        try:
            while True:
                events = self._selector.select()

                for key, mask in events:
                    # accept new client
                    callback, namespace = key.data
                    try:
                        if namespace is None:
                            callback(key.fileobj)
                        else:
                            callback(key.fileobj, namespace)
                    except exceptions.ExitWrite:  # on client/server closed
                        pass
                self._clean_write_queue()
        except KeyboardInterrupt:  # when start debug mode listen Ctrl-C
            logger.info('<Ctrl + C> Bye, Never BUG')
            exit()
        except Exception as e:
            logger.error('Fatal Error occurs for {}'.format(repr(e)))
            raise

    def _accept_client(self, server_fd):
        # accept new client
        client_fd, client_address = server_fd.accept()
        # logger
        logger.debug('Client({}:{}) connecting'.format(*client_address))
        # set non=blocking
        client_fd.setblocking(False)
        # register listen EVENT_READ
        self._selector.register(client_fd,
                                selectors.EVENT_READ,
                                (self._accept_http_handshake, None))

        # close information
        self._close_information[client_fd] = (None, False)
        # write queue for single socket descriptor
        self._write_queue[client_fd] = deque()  # type: deque
        # create tcp stream class
        self._client_list['default'][client_fd] = \
            tcp_stream.TCPStream(client_fd)

    def _accept_http_handshake(self, socket_fd):
        _tcp_stream = \
            self._client_list['default'][socket_fd]  # type:tcp_stream.TCPStream
        # receive data from kernel tcp buffer
        pos = _tcp_stream.find_buffer(b'\r\n\r\n')
        if pos is -1:
            return
        http_request = http_message.factory_http_message(
            _tcp_stream.feed_buffer(pos))
        # Verify http request is correct
        support_extension = tuple()
        try:
            support_extension_list = \
                http_verifier.verify_request(
                    socket_fd.getpeername(), http_request)
            support_extension = (
                b'Sec-WebSocket-Extensions',
                b','.join(map(
                    lambda x: generic.to_bytes(x), support_extension_list)))
            if not support_extension[1]:
                support_extension = None
        except exceptions.HttpVerifierError:
            http_response = http_message.HttpResponse(
                403, (b'X-Forbidden-Reason', b'http-options-invalid'))
            # verify error occurs
            self._socket_ready_write(
                socket_fd, http_response, http_request.url_path)
            self._close_client(socket_fd, 'default')
        logger.debug('Request: {}'.format(repr(http_request)))
        # TODO. chunk header-field
        if 'Content-Length' in http_request.header:
            logger.info('Request has payload, length = {}'.format(
                http_request.header.get_value('Content-Length')))
            # buffer length is too short
            if _tcp_stream.get_buffer_length() < \
                    http_request.header.get_value('Content-Length'):
                return
            # drop payload data
            _tcp_stream.feed_buffer(http_request['Content-Length'].value)

        ws_key = http_request.header.get_value('Sec-WebSocket-Key')
        # Optionally, other header fields, such as those used to send
        # cookies or request authentication to a server.
        http_response = http_message.HttpResponse(
            101, *(
                (b'Upgrade', b'websocket'),
                (b'Connection', b'Upgrade'),
                (b'Sec-WebSocket-Accept', ws_utils.ws_accept_key(ws_key)),
                support_extension
            )
        )
        try:
            namespace = generic.to_string(http_request.url_path)
            # get handler or default handler
            _handler = self._router.solution(namespace, 'handler')(socket_fd)
            # get controller or default controller
            controller_name = self._router.solution(namespace, 'controller')
            # initial controller
            if namespace not in self._client_list:
                self._client_list[namespace] = dict()
            self._client_list[namespace][socket_fd] = controller_name(
                self._client_list['default'].pop(socket_fd),
                self._write_queue[socket_fd].append,
                _handler)
            # send http-handshake-response
            self._write_queue[socket_fd].append(http_response)
            # notification handler connect event
            response = _handler.on_connect()
            # send connect message
            if hasattr(response, 'pack'):
                self._write_queue[socket_fd].append(response)
            elif hasattr(response, 'generate_frame'):
                self._write_queue[socket_fd].append(response.generate_frame)
            # modify selector data
            self._selector.modify(socket_fd,
                                  selectors.EVENT_READ,
                                  (self._socket_ready_receive, namespace))
        except exceptions.ParameterError:
            raise exceptions.FatalError('handler not found')

    def _socket_ready_receive(self, socket_fd, namespace):
        try:
            controller = \
                self._client_list[namespace][socket_fd]  # type: BaseController
            controller.ready_receive()
        except exceptions.ConnectClosed as e:
            # from server close
            if self._close_information[socket_fd][0] is None:
                # TODO. handler send close-frame
                if e.args[0][0] == 1000:
                    # client first send close-frame
                    self._close_information[socket_fd] = ('client', False)
            else:
                self._close_information[socket_fd] = \
                            (self._close_information[socket_fd][0], True)
                self._close_client(socket_fd, namespace)

            if e.args[0][0] != 1000:
                logger.info('Server active close-frame, reason({})'.format(
                    e.args[0][0]))

            self._write_queue[socket_fd].append(ws_frame.generate_close_frame(
                extra_data=e.args[0][1], errno=e.args[0][0]))

    def _clean_write_queue(self):
        _clients = dict()
        for namespace in self._client_list:
            for socket_fd in self._client_list[namespace].keys():
                _clients[socket_fd] = namespace
        for socket_fd, namespace in _clients.items():
            while len(self._write_queue[socket_fd]):
                try:
                    self._socket_ready_write(
                        socket_fd, self._write_queue[socket_fd].popleft(),
                        namespace)
                except exceptions.ExitWrite:
                    break

    def _socket_ready_write(self, socket_fd, data_pack, namespace: str):
        try:
            if isinstance(data_pack, ws_frame.FrameBase):
                if data_pack.frame_type == ws_frame.Close_Frame:
                    # from server(normal or error occurs) first send close-frame
                    if self._close_information[socket_fd][0] is None:
                        self._close_information[socket_fd] = ('server', False)
                    else:
                        self._close_information[socket_fd] = (
                            self._close_information[socket_fd][0], True)
            if hasattr(data_pack, 'pack'):
                logger.debug('Response: {}'.format(data_pack))
                socket_fd.sendall(data_pack.pack())
            else:
                raise exceptions.SendDataPackError('data pack invalid')
            if self._close_information[socket_fd][1] is True:
                self._close_client(socket_fd, namespace)
        except Exception:
            raise

    def _close_client(self, socket_fd, namespace):
        logger.debug('Client({}:{}) socket fd closed'.format(
            *socket_fd.getpeername()))

        self._selector.unregister(socket_fd)
        self._client_list[namespace].pop(socket_fd)
        self._write_queue.pop(socket_fd)
        self._close_information.pop(socket_fd)
        socket_fd.close()
        raise exceptions.ExitWrite()


class WebSocketServer(WebSocketServerBase):

    def __init__(self, host, port, *, debug=False, server_name=None):
        self._debug = bool(debug)
        if os.name == 'nt':
            logger.wait_logger_init_msg(
                logger.warning,
                'WebSocketServer running in Windows, only DEBUG mode')
            self._debug = True
        if server_name is None:
            server_name = host
        http_verifier.set_server_name(server_name, port=port)
        super(WebSocketServer, self).__init__(host, port, debug=self._debug)

    def broadcast(self, message, include_self: bool=False):
        _self_class = self._get_handler_self()

        if not hasattr(_self_class, '__namespace__'):
            raise exceptions.BroadcastError('broadcast context invalid')

        namespace = _self_class.__namespace__
        if namespace not in self._client_list:
            raise exceptions.FatalError('Fatal error occurs, please report')

        if hasattr(message, 'pack'):
            pass
        elif hasattr(message, 'generate_frame'):
            message = message.generate_frame
        else:
            raise exceptions.BroadcastError('broadcast message invalid')

        _context_socket_fd = _self_class.socket_fd
        for socket_fd in self._client_list[namespace]:
            if socket_fd == _context_socket_fd and not include_self:
                continue
            self._write_queue[socket_fd].append(message)
        return True

    def client_count(self):
        _self_class = self._get_handler_self()

        if not hasattr(_self_class, '__namespace__'):
            raise exceptions.BroadcastError('broadcast context invalid')

        namespace = _self_class.__namespace__
        if namespace not in self._client_list:
            return 1
        return len(self._client_list[namespace]) + 1  # and current connection

    @staticmethod
    def _get_handler_self():
        prev_locals = inspect.stack()[2][0].f_locals
        if 'self' in prev_locals:
            _self_class = prev_locals['self']
            return _self_class
        raise exceptions.FatalError('cannot find handler class')

    @property
    def is_debug(self):
        return self._debug

    @staticmethod
    def disable_http_verifier():
        return http_verifier.disable()

    @staticmethod
    def enable_http_verifier():
        return http_verifier.enable()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type and exc_tb:
            raise exc_val


def create_websocket_server(host='localhost', port=8999, *, debug=False,
                            logging_level='info', log_file=None,
                            server_name=True):
    with WebSocketServer(host, port, debug=debug,
                         server_name=server_name) as server:
        logger.init(logging_level, server.is_debug, log_file)
        return server
