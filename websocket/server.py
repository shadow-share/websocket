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
'''

First fragment

    FIN = 0, opcode = 1     # opcode = 1(text frame)


Second fragment

    FIN = 0, opcode = 0     # opcode = 0(continuation frame)


Third fragment

    FIN = 1, opcode = 0     # opcode = 0(continuation frame)

'''

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
import select
import signal
import socket
import selectors
from collections import deque, OrderedDict

from websocket.utils import (
    exceptions, logger
)
from websocket.ext import handler
from websocket.net import ws_frame
from websocket.controller import plain_spliter


__all__ = [ 'create_websocket_server' ]


class Deamon(object):

    def __init__(self, *, debug = False, pid_file:str = None,
                 stdin:str = '/dev/null',
                 stdout:str = '/dev/null',
                 stderr:str = '/dev/null'):
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
        if self._debug is False and (os.name == 'nt' or not hasattr(os, 'fork')):
            raise exceptions.DeamonError('Windows does not support fork')
        # double fork create a deamon
        try:
            pid = os.fork()  # fork #1
            if pid > 0: # parent exit
                exit()
        except OSError as e:
            raise exceptions.FatalError(
                'Fork #1 error occurs, reason({})'.format(e))

        os.chdir('/')
        os.setsid()
        os.umask(0)

        try:
            pid = os.fork()  # fork #2
            if pid > 0: # parent exit
                exit()
        except OSError as e:
            raise exceptions.FatalError(
                'Fork #2 error occurs, reason({})'.format(e))

        # redirect all std file descriptor
        sys.stdout.flush()
        sys.stderr.flush()
        _stdin = open(self._stdin, 'r')
        _stdout = open(self._stdout, 'a')
        _stderr = open(self._stderr, 'wb+', buffering = 0)
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
            fd.write('{pid}\n'.format(pid = os.getpid()))
        logger.info('Daemon has been started')


    def _signal_handler(self, signum, frame):
        logger.info('Deamon receive an exit signal')
        self._remove_pid_file()
        exit()


    def _remove_pid_file(self):
        logger.info('Deamon has exited')
        if os.path.exists(self._pid_file):
            os.remove(self._pid_file)


class WebSocketServerBase(Deamon, metaclass = abc.ABCMeta):

    # max listen queue size
    LISTEN_SIZE = 16

    def __init__(self, host, port, *, pid_file = None, debug = False):
        # start deamon
        super(WebSocketServerBase, self).__init__(pid_file = pid_file,
                                                  debug = debug)
        # all handshake client
        self._client_list = {} # type: dict()
        # Server address information
        self._server_address = (host, port) # type: tuple
        # Write queue
        self._write_queue = OrderedDict()
        # handler initialize
        self._handlers = None # type: tuple()
        # close frame information (from_endpoint, is receive/send close)
        self._close_information = (None, False)


    def set_handler(self, ws_handlers):
        if not isinstance(ws_handlers, handler.WebSocketHandlerProtocol):
            if isinstance(ws_handlers, (tuple, list)) and len(ws_handlers) is 4:
                self._handlers = tuple(ws_handlers)
                return
            raise TypeError('handlers must be derived with WebSocketHandlerProtocol')
        self._handlers = ws_handlers.export()


    def set_controller(self, controller:str):
        pass


    # TODO. controller
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
        # in the begin, read-list have only server socket
        self._rl, self._wl, self._xl = deque([self._server_fd]), deque(), deque()

        try:
            while True:
                # TODO. using selector module
                # selectors.BaseSelector()
                rl, wl, el = select.select(self._rl, self._wl, self._xl)

                self._read_list_handler(rl)
                self._write_list_handler(wl)
                self._error_list_handler(el)
        except KeyboardInterrupt: # when start debug mode check Ctrl-C
            logger.info('<Ctrl + C> Bye, Never BUG')
            exit()


    def _read_list_handler(self, rl):
        for readable_fd in rl:
            if readable_fd == self._server_fd:
                self._accept_client()
                continue

            if readable_fd in self._client_list:
                self._socket_ready_receive(readable_fd)
                continue

            # write queue for single socket descriptor
            self._write_queue[readable_fd] = deque() # type: deque
            # Received data is an HTTP request
            self._client_list[readable_fd] = plain_spliter.PlainController(
                readable_fd, self._write_queue[readable_fd].append,
                *self._handlers)


    def _socket_ready_receive(self, socket_fd):
        try:
            self._client_list[socket_fd].ready_receive()
        except exceptions.ConnectClosed as e:
            # from server close
            if self._close_information[0] is None:
                # TODO. handler send close-frame
                if e.args[0][0] == 1000:
                    # client first send close-frame
                    self._close_information = ('client', False)
            else:
                self._close_information = (self._close_information[0], True)
                self._close_client(socket_fd)

            if e.args[0][0] != 1000:
                logger.info('Server active close-frame, reason({})'.format(
                    e.args[0][0]))

            self._write_queue[socket_fd].append(ws_frame.generate_close_frame(
                extra_data = e.args[0][1], errno = e.args[0][0]))


    def _write_list_handler(self, wl):
        for writeable_fd in wl:
            if writeable_fd in self._client_list:
                while len(self._write_queue[writeable_fd]):
                    # first call ChildClass::_send_frame
                    self._socket_ready_write(writeable_fd,
                                self._write_queue[writeable_fd].popleft())


    # Process Close Request
    def _socket_ready_write(self, socket_fd, data_pack:ws_frame.FrameBase):
        try:
            if isinstance(data_pack, ws_frame.FrameBase) and \
                            data_pack.frame_type == ws_frame.Close_Frame:
                # from server(normal or error occurs) first send close-frame
                if self._close_information[0] is None:
                    self._close_information = ('server', False)
                else:
                    self._close_information = (self._close_information[0], True)
                self._wl.remove(socket_fd)
            if hasattr(data_pack, 'pack'):
                logger.debug('Response: {}'.format(data_pack))
                socket_fd.sendall(data_pack.pack())
            else:
                raise exceptions.SendDataPackError('data pack invalid')
            if self._close_information[1] is True:
                self._close_client(socket_fd)
        except Exception:
            raise


    def _error_list_handler(self, el):
        pass


    def _accept_client(self):
        # accept new client
        client_fd, client_address = self._server_fd.accept()
        # append to read_list and write_list
        self._rl.append(client_fd)
        self._wl.append(client_fd)

    def _close_client(self, socket_fd):
        logger.debug('Client({}:{}) socket fd closed'.format(
            *socket_fd.getpeername()))

        if socket_fd in self._rl:
            self._rl.remove(socket_fd)
        if socket_fd in self._wl:
            self._wl.remove(socket_fd)
        self._client_list.pop(socket_fd)
        socket_fd.close()


class WebSocketServer(WebSocketServerBase):

    def __init__(self, host, port, *, debug = False):
        self._debug = bool(debug)
        if os.name == 'nt':
            logger._wait_logger_init_msg(logger.warning,
                 'WebSocketServer running in Windows, only DEBUG mode')
            self._debug = True
        super(WebSocketServer, self).__init__(host, port, debug = self._debug)


    # On receive frame called.
    def _socket_ready_receive(self, socket_fd):
        # other operate
        super(WebSocketServer, self)._socket_ready_receive(socket_fd)


    # Send frame process
    def _socket_ready_write(self, socket_fd, data_pack:ws_frame.FrameBase):
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


def create_websocket_server(host = 'localhost', port = 8999, *, debug = False,
                            logging_level = 'info', log_file = None):
    with WebSocketServer(host, port, debug = debug) as server:
        logger.init(logging_level, server.is_debug, log_file)
        return server

