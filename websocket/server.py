#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#

# Optionally, a |Sec-WebSocket-Extensions| header field, with a
# list of values indicating which extensions the client would like
# to speak.

# Optionally, other header fields, such as those used to send
# cookies or request authentication to a server.  Unknown header
# fields are ignored

# If the connection is happening on an HTTPS (HTTP-over-TLS) port,
# perform a TLS handshake over the connection.

# The |Origin| header field in the client's handshake indicates
# the origin of the script establishing the connection. If the
# server does not validate the origin, it will accept connections
# from anywhere.  If the server does not wish to accept this
# connection, it MUST return an appropriate HTTP error code
# (e.g., 403 Forbidden) and abort the WebSocket handshake
# described in this section.

# https://tools.ietf.org/html/rfc6455#section-4.2.2 - /Version/

#  The absence of such a field is equivalent to the null value
# (meaning that if the server does not wish to agree to one of
# the suggested subprotocols, it MUST NOT send back a
# |Sec-WebSocket-Protocol| header field in its response).
# The empty string is not the same as the null value for these
# purposes and is not a legal value for this field.

# Supporting Multiple Versions of WebSocket Protocol


# a client MUST mask all frames that it sends to the server.  (Note
# that masking is done whether or not the WebSocket Protocol is running
# over TLS.)  The server MUST close the connection upon receiving a
# frame that is not masked.  In this case, a server MAY send a Close
# frame with a status code of 1002 (protocol error)

# A server MUST NOT mask any frames that it sends to
# the client.  A client MUST close a connection if it detects a masked
# frame.

# An unfragmented message consists of a single frame with the FIN
# bit set (Section 5.2) and an opcode other than 0.

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

# Control frames (see Section 5.5) MAY be injected in the middle of
# a fragmented message.  Control frames themselves MUST NOT be
# fragmented.

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

# As control frames cannot be fragmented, an intermediary MUST NOT
# attempt to change the fragmentation of a control frame.

# An intermediary MUST NOT change the fragmentation of a message if
# any reserved bit values are used and the meaning of these values
# is not known to the intermediary.

# IMPLEMENTATION NOTE: In the absence of any extension, a receiver
# doesn't have to buffer the whole frame in order to process it.  For
# example, if a streaming API is used, a part of a frame can be
# delivered to the application.  However, note that this assumption
# might not hold true for all future WebSocket extensions.

# All control frames MUST have a payload length of 125 bytes or less
# and MUST NOT be fragmented.


#  Sending and Receiving Data

# The endpoint MUST ensure the WebSocket connection is in the OPEN
# state (cf. Sections 4.1 and 4.2.2.)  If at any point the state of
# the WebSocket connection changes, the endpoint MUST abort the
# following steps.

# If the data is being sent by the client, the frame(s) MUST be masked
import os
import abc
import sys
import atexit
import signal
import socket
import functools
import selectors
from collections import deque, OrderedDict
from websocket.utils import (
    exceptions, logger, ws_utils, generic
)
from websocket.ext import handler, router
from websocket.net import (
    ws_frame, tcp_stream, http_message
)
from websocket.controller import (
    base_controller, plain_controller
)


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

        # set signal handler
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGILL, self._signal_handler)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        # register function at exit
        atexit.register(self._remove_pid_file)
        with open(self._pid_file, 'w') as fd:
            fd.write('{pid}\n'.format(pid=os.getpid()))
        logger.info('Daemon has been started')

    def _signal_handler(self, signum, frame):
        logger.info('Deamon receive an exit signal({}: {})'.format(
            signum, frame))
        self._remove_pid_file()
        exit()

    def _remove_pid_file(self):
        logger.info('Deamon has exited')
        if os.path.exists(self._pid_file):
            os.remove(self._pid_file)


class WebSocketServerBase(Daemon, metaclass=abc.ABCMeta):

    # max listen queue size
    LISTEN_SIZE = 16

    def __init__(self, host, port, *, pid_file=None, debug=False):
        # start deamon
        super(WebSocketServerBase, self).__init__(pid_file=pid_file,
                                                  debug=debug)
        # server file descriptor
        self._server_fd = None  # type: socket.socket
        # all handshake client
        self._client_list = {}  # type: dict()
        # Server address information
        self._server_address = (host, port)  # type: tuple
        # Write queue
        self._write_queue = OrderedDict()
        # close frame information (from_endpoint, is receive/send close)
        self._close_information = dict()
        # router object
        self._router = router.Router()
        # register default handler
        self._router.register_default('controller',
                                      plain_controller.PlainController)

    def register_handler(self, namespace):
        exceptions.raise_parameter_error('namespace', str, namespace)

        def _decorator_wrapper(class_object):
            # isinstance(class_object, handler.WebSocketHandlerProtocol) False
            if handler.WebSocketHandlerProtocol not in class_object.__bases__:
                raise exceptions.ParameterError(
                    'handlers must be derived with WebSocketHandlerProtocol')
            self._router.register(namespace, 'handler', class_object)

            @functools.wraps(class_object)
            def _handler_wrapper(*args, **kwargs):
                logger.info('{} handler register on {}'.format(
                    class_object.__name__, namespace))
                return class_object(*args, **kwargs)
            return _handler_wrapper
        return _decorator_wrapper

    def register_default_handler(self, class_object):
        if handler.WebSocketHandlerProtocol not in class_object.__bases__:
            raise exceptions.ParameterError(
                'handlers must be derived with WebSocketHandlerProtocol')
        logger.info('Default handler registered for {}'.format(
            class_object.__name__))
        self._router.register_default('handler', class_object)

        @functools.wraps(class_object)
        def _handler_wrapper(*args, **kwargs):
            return class_object(*args, **kwargs)
        return _handler_wrapper

    def register_controller(self, namespace, controller_name):
        exceptions.raise_parameter_error('namespace', str, namespace)
        if base_controller.BaseController not in controller_name.__bases__:
            raise exceptions.ParameterError(
                'handlers must be derived with WebSocketHandlerProtocol')
        self._router.register(namespace, 'controller', controller_name)

    def register_default_controller(self, controller_name):
        if base_controller.BaseController not in controller_name.__bases__:
            raise exceptions.ParameterError(
                'handlers must be derived with WebSocketHandlerProtocol')
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
        self._selector.register(self._server_fd,
                                selectors.EVENT_READ, self._accept_client)

        try:
            while True:
                events = self._selector.select()

                for key, mask in events:
                    # accept new client
                    callback = key.data
                    callback(key.fileobj)
                self._clean_write_queue()
        except KeyboardInterrupt:  # when start debug mode listen Ctrl-C
            logger.info('<Ctrl + C> Bye, Never BUG')
            exit()
        except Exception as e:
            logger.error('Error occurs for {}'.format(repr(e)))
            raise

    def _accept_client(self, server_fd):
        # accept new client
        client_fd, client_address = server_fd.accept()
        # logger
        logger.debug('Client({}:{}) connecting, fileno = {}'.format(
            *client_address, client_fd.fileno()))
        # set non=blocking
        client_fd.setblocking(False)
        # register listen EVENT_READ
        self._selector.register(client_fd,
                                selectors.EVENT_READ,
                                self._accept_http_handshake)

        # record close information
        self._close_information[client_fd] = (None, False)
        # write queue for single socket descriptor
        self._write_queue[client_fd] = deque()  # type: deque
        # Received data is an HTTP request
        self._client_list[client_fd] = tcp_stream.TCPStream(client_fd)
        # TODO. accept http request need outside
        # self._client_list[client_fd] = plain_controller.PlainController(
        #     client_fd, self._write_queue[client_fd].append, *self._handlers)

    def _accept_http_handshake(self, socket_fd):
        _tcp_stream = self._client_list[socket_fd]  # type: tcp_stream.TCPStream
        # receive data from kernel tcp buffer
        _tcp_stream.ready_receive()
        pos = _tcp_stream.find_buffer(b'\r\n\r\n')
        if pos is -1:
            return
        http_request = http_message.factory(_tcp_stream.feed_buffer(pos))
        logger.debug('Request: {}'.format(repr(http_request)))
        # TODO. chunk header-field
        if 'Content-Length' in http_request:
            print('have any payload', http_request['Content-Length'].value)
            # drop payload data
            # TODO. payload data send to connect handler
            _tcp_stream.feed_buffer(http_request['Content-Length'].value)

        ws_key = http_request[b'Sec-WebSocket-Key']
        http_response = http_message.HttpResponse(
            101, *http_message.create_header_fields(
                (b'Upgrade', b'websocket'),
                (b'Connection', b'Upgrade'),
                (b'Sec-WebSocket-Accept', ws_utils.ws_accept_key(ws_key.value))
            )
        )
        _handler = self._router.solution(
            generic.to_string(http_request.resource), 'handler')()
        _handler.on_connect(socket_fd.getpeername())
        self._write_queue[socket_fd].append(http_response)
        controller_name = self._router.solution(
            generic.to_string(http_request.resource), 'controller')
        self._client_list[socket_fd] = controller_name(
            self._client_list[socket_fd], self._write_queue[socket_fd].append,
            _handler)
        self._selector.modify(socket_fd, selectors.EVENT_READ,
                              self._socket_ready_receive)

    def _socket_ready_receive(self, socket_fd):
        try:
            self._client_list[socket_fd].ready_receive()
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
                self._close_client(socket_fd)

            if e.args[0][0] != 1000:
                logger.info('Server active close-frame, reason({})'.format(
                    e.args[0][0]))

            self._write_queue[socket_fd].append(ws_frame.generate_close_frame(
                extra_data=e.args[0][1], errno=e.args[0][0]))

    def _clean_write_queue(self):
        _clients = list(self._client_list.keys())
        for write_fd in _clients:
            while len(self._write_queue[write_fd]):
                # first call ChildClass::_send_frame
                self._socket_ready_write(write_fd,
                                         self._write_queue[write_fd].popleft())

    def _socket_ready_write(self, socket_fd, data_pack: ws_frame.FrameBase):
        try:
            if isinstance(data_pack, ws_frame.FrameBase) and \
                            data_pack.frame_type == ws_frame.Close_Frame:
                # from server(normal or error occurs) first send close-frame
                if self._close_information[socket_fd][0] is None:
                    self._close_information[socket_fd] = ('server', False)
                else:
                    self._close_information[socket_fd] = \
                                (self._close_information[socket_fd][0], True)
            if hasattr(data_pack, 'pack'):
                logger.debug('Response: {}'.format(data_pack))
                socket_fd.sendall(data_pack.pack())
            else:
                raise exceptions.SendDataPackError('data pack invalid')
            if self._close_information[socket_fd][1] is True:
                self._close_client(socket_fd)
        except Exception:
            raise

    def _close_client(self, socket_fd):
        logger.debug('Client({}:{}) socket fd closed'.format(
            *socket_fd.getpeername()))

        self._selector.unregister(socket_fd)
        self._client_list.pop(socket_fd)
        self._close_information.pop(socket_fd)
        socket_fd.close()


class WebSocketServer(WebSocketServerBase):

    def __init__(self, host, port, *, debug=False):
        self._debug = bool(debug)
        if os.name == 'nt':
            logger.wait_logger_init_msg(
                logger.warning,
                'WebSocketServer running in Windows, only DEBUG mode')
            self._debug = True
        super(WebSocketServer, self).__init__(host, port, debug=self._debug)

    # On receive frame called.
    def _socket_ready_receive(self, socket_fd):
        # other operate
        super(WebSocketServer, self)._socket_ready_receive(socket_fd)

    # Send frame process
    def _socket_ready_write(self, socket_fd, data_pack: ws_frame.FrameBase):
        # other operate
        super(WebSocketServer, self)._socket_ready_write(socket_fd, data_pack)

    @property
    def is_debug(self):
        return self._debug

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type and exc_tb:
            raise exc_val


def create_websocket_server(host='localhost', port=8999, *, debug=False,
                            logging_level='info', log_file=None):
    with WebSocketServer(host, port, debug=debug) as server:
        logger.init(logging_level, server.is_debug, log_file)
        return server
