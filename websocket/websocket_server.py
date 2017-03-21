# !/usr/bin/env python3
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

# If the data is being sent by the client, the frame(s) MUST be
# masked as defined in Section 5.3.

import os
import abc
import sys
import atexit
import select
import signal
import socket
import logging
from collections import deque, OrderedDict
from websocket.distributer import Distributer
from websocket import utils, frame, exceptions, websocket_handler


class Deamon(object):

    def __init__(self, *, debug = False,
                 stdin:str = '/dev/null',
                 stdout:str = '/dev/null',
                 stderr:str = '/dev/null',
                 pid_file:str = '/tmp/python_websocket.pid'):
        self._debug = debug
        self._stdin = stdin  # type: str
        self._stdout = stdout  # type: str
        self._stderr = stderr  # type: str
        self._pid_file = pid_file  # type: str


    def run_forever(self):
        if not self._debug and os.path.exists(self._pid_file):
            raise exceptions.DeamonError(
                'pid file already exists, Deamon running?')
        elif self._debug:
            # logging
            utils.warning_msg('Debugger is active!')
        else:
            self._start_deamon()


    def _start_deamon(self):
        if os.name == 'nt' or not hasattr(os, 'fork'):
            raise exceptions.DeamonError('Windows does not support fork.')
        # double fork create a deamon
        try:
            pid = os.fork()  # fork #1
            if pid > 0:
                exit()
        except OSError as e:
            raise exceptions.FatalError('Fork #1 error occurs, {}:{}'.format(
                e.errno, e.error))

        os.chdir('/')
        os.setsid()
        os.umask(0)

        try:
            pid = os.fork()  # fork #2
            if pid > 0:
                exit()
        except OSError as e:
            raise exceptions.FatalError('Fork #1 error occurs, {}:{}'.format(
                e.errno, e.error))

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
        with open(self._pid_file, 'a+') as fd:
            fd.write('{pid}\n'.format(pid = os.getpid()))
        utils.info_msg('Daemon has been started')


    def _signal_handler(self, signum, frame):
        utils.info_msg('Server receive an exit signal')
        self._remove_pid_file()


    def _remove_pid_file(self):
        utils.info_msg('Server has exited')
        if os.path.exists(self._pid_file):
            os.remove(self._pid_file)
        exit()


class WebSocket_Server_Base(Deamon, metaclass = abc.ABCMeta):

    def __init__(self, host, port, *, pid_file = None, debug = False):
        # start deamon
        if pid_file is not None:
            super(WebSocket_Server_Base, self).__init__(pid_file = pid_file,
                                                        debug = debug)
        else:
            super(WebSocket_Server_Base, self).__init__(debug = debug)
        # all handshake client
        self._client_list = {} # type: dict()
        # Server address information
        self._server_address = (host, port) # type: tuple
        # Write queue
        self._write_queue = OrderedDict()
        # handler initialize
        self._handlers = None # type: tuple()


    def set_handler(self, ws_handlers):
        if not isinstance(ws_handlers, websocket_handler.WebSocket_Handler):
            raise TypeError('handlers must be derived with WebSocket_Handler')
        self._handlers = (
            ws_handlers.on_connect,
            ws_handlers.on_message,
            ws_handlers.on_close,
            ws_handlers.on_error
        )


    def run_forever(self):
        super(WebSocket_Server_Base, self).run_forever()
        # Create server socket file descriptor
        self._server_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Set socket option, REUSEADDR = True
        self._server_fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Set using non-block socket
        self._server_fd.setblocking(False)
        # Start server
        self._server_fd.bind(self._server_address)
        self._server_fd.listen(16)
        utils.info_msg('Server run {}:{}'.format(*self._server_address))
        # enter the main loop
        self._select_loop()


    def _select_loop(self):
        # in the begin, read-list have only server socket
        self._rl, self._wl, self._xl = deque([self._server_fd]), deque(), deque()

        while True:
            rl, wl, el = select.select(self._rl, self._wl, self._xl)

            self._read_list_handler(rl)
            self._write_list_handler(wl)
            self._error_list_handler(el)


    def _read_list_handler(self, rl):
        for readable_fd in rl:
            if readable_fd == self._server_fd:
                self._accept_client()
                continue

            if readable_fd in self._client_list:
                self._frame_distribute(readable_fd)
                continue

            # write queue for single socket descriptor
            self._write_queue[readable_fd] = deque() # type: deque
            # Received data is an HTTP request
            self._client_list[readable_fd] = Distributer(readable_fd,
                self._write_queue[readable_fd].append, *self._handlers)


    def _frame_distribute(self, socket_fd):
        try:
            self._client_list[socket_fd].ready_receive()
        except exceptions.ConnectClosed as e:
            if e.args[0][0] != 1000:
                utils.info_msg('Client({}:{}) closed'.format(
                    *socket_fd.getpeername()))
            self._write_queue[socket_fd].append(frame.generate_close_frame(
                extra_data = e.args[0][1], errno = e.args[0][0]))


    # Process Close Request
    def _send_frame(self, socket_fd, send_frame:frame.FrameBase):
        try:
            if isinstance(send_frame, frame.FrameBase) and \
                            send_frame.frame_type == frame.Close_Frame:
                self._client_list.pop(socket_fd)
                self._rl.remove(socket_fd)
                self._wl.remove(socket_fd)

            # Normal send frame
            if isinstance(send_frame, frame.FrameBase):
                socket_fd.sendall(send_frame.pack())
            elif hasattr(send_frame, 'pack'):
                socket_fd.sendall(send_frame.pack())
            else:
                print(send_frame)
                raise exceptions.SendFrameError('send frame is not base Frame')
        except Exception as e:
            pass


    def _write_list_handler(self, wl):
        for writeable_fd in self._write_queue:
            if writeable_fd in wl:
                while len(self._write_queue[writeable_fd]):
                    # first call ChildClass::_send_frame
                    self._send_frame(
                        writeable_fd,
                        self._write_queue[writeable_fd].popleft())


    def _error_list_handler(self, el):
        pass


    def _accept_client(self):
        # accept new client
        client_fd, client_address = self._server_fd.accept()
        # append to read_list and write_list
        self._rl.append(client_fd)
        self._wl.append(client_fd)


class WebSocket_Simple_Server(WebSocket_Server_Base):

    def __init__(self, host, port, *, debug = False):
        self._debug_mode = bool(debug)
        if os.name == 'nt':
            utils._wait_logger_init_msg(utils.warning_msg, 'WSServer running'
                                        + 'in Windows, only DEBUG mode')
            self._debug_mode = True
        super(WebSocket_Simple_Server, self).__init__(host, port,
                                                      debug = self._debug_mode)


    # On receive frame called.
    def _frame_distribute(self, socket_fd):
        # other operate
        super(WebSocket_Simple_Server, self)._frame_distribute(socket_fd)


    # Send frame process
    def _send_frame(self, socket_fd, send_frame):
        # other operate
        super(WebSocket_Simple_Server, self)._send_frame(socket_fd, send_frame)


    @property
    def is_debug(self):
        return self._debug_mode


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type and exc_tb:
            raise exc_val


def create_websocket_server(host = 'localhost', port = 8999, *,
                            debug = False,
                            logging_level = logging.INFO,
                            log_file = None):
    with WebSocket_Simple_Server(host, port, debug = debug) as server:
        utils.logger_init(logging_level, console = server.is_debug,
                          log_file = log_file)
        return server


def create_websocket_event_server():
    pass

