#!/usr/bin/env python3
#
# Copyright (C) 2017 ShadowMan
#

# An HTTP/1.1 or higher GET request, including a "Request-URI"

# A |Host| header fieldt containing the server's authoriy.

# An |Upgrade| header field containing the value "websocket",
# treated as an ASCII case-insensitive value.

# A |Connection| header field that includes the token "Upgrade",
# treated as an ASCII case-insensitive value.

# A |Sec-WebSocket-Key| header field with a base64-encoded (see
# Section 4 of [RFC4648]) value that, when decoded, is 16 bytes in
# length.

# A |Sec-WebSocket-Version| header field, with a value of 13.

# Optionally, an |Origin| header field.  This header field is sent
# by all browser clients.  A connection attempt lacking this
# header field SHOULD NOT be interpreted as coming from a browser
# client.

# Optionally, a |Sec-WebSocket-Protocol| header field, with a list
# of values indicating which protocols the client would like to
# speak, ordered by preference.

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

import abc
import select
import socket
import logging
from collections import deque, OrderedDict
from websocket import utils, frame, http, websocket_utils,\
    distributer, exceptions, websocket_handler

class WebSocket_Server_Base(object, metaclass = abc.ABCMeta):

    def __init__(self, host, port):
        # all handshake client
        self._client_list = {}
        # Server address information
        self._server_address = (host, port)
        # Write queue
        self._write_queue = OrderedDict()
        # handler initialize
        self._on_connect = None
        self._on_message = None
        self._on_close = None
        self._on_error = None
        # http request instance
        self._http_request = None


    def set_handler(self, ws_handlers):
        if not isinstance(ws_handlers, websocket_handler.WebSocket_Handler):
            raise TypeError('the websocket handlers must be base on WebSocket_Handler')
        self._on_connect = ws_handlers.on_connect
        self._on_message = ws_handlers.on_message
        self._on_close = ws_handlers.on_close
        self._on_error = ws_handlers.on_error


    def run_forever(self):
        # Create server socket file descriptor
        self._server_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Set socket option, REUSEADDR = True
        self._server_fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Set using non-block socket
        self._server_fd.setblocking(False)
        # Start server
        self._server_fd.bind(self._server_address)
        self._server_fd.listen(16)
        # enter the main loop
        self._select_loop()


    def _select_loop(self):
        # in the begin, read-list have only server socket
        self._rl, self._wl, self._xl = deque([ self._server_fd ]), deque(), deque()

        while True:
            rl, wl, el = select.select(self._rl, self._wl, self._xl)

            self._read_list_handler(rl)
            self._write_list_handler(wl)
            self._error_list_handler(el)


    def _read_list_handler(self, rl):
        for readable_fd in rl:
            if readable_fd == self._server_fd:
                self._accept_client()
            else:
                if readable_fd in self._client_list:
                    self._frame_distribute(readable_fd, frame.Frame_Parser(readable_fd))
                else:
                    # write queue for single socket descriptor
                    self._write_queue[readable_fd] = deque()
                    # Received data is an HTTP request
                    self._client_list[readable_fd] = distributer.Distributer(
                        readable_fd, # socket file descriptor
                        self._write_queue[readable_fd].append, # send method
                        self._on_connect, # connect established handler
                        self._on_message, # message received handler
                        self._on_close, # connect close handler
                        self._on_error # error occurs handler
                    )
                    self._http_request = self._client_list[readable_fd].get_http_request()
                    self._http_request_checker()


    def _http_request_checker(self):
        self._check_http_version()


    def _check_http_version(self):
        pass


    def _check_origin(self):
        pass


    def _check_host(self):
        pass


    def _frame_distribute(self, socket_fd, receive_frame):
        pass


    @abc.abstractclassmethod
    def _send_frame(self, socket_fd, send_frame):
        pass


    def _write_list_handler(self, wl):
        for writeable_fd in self._write_queue:
            if writeable_fd in wl:
                while len(self._write_queue[writeable_fd]):
                    self._send_frame(writeable_fd, self._write_queue[writeable_fd].popleft())


    def _error_list_handler(self, el):
        pass


    def _close_fd(self, socket_fd):
        self._rl.remove(socket_fd)
        self._wl.remove(socket_fd)
        socket_fd.close()


    def _accept_client(self):
        # accept new client
        client_fd, client_address = self._server_fd.accept()
        # append to read_list and write_list
        self._rl.append(client_fd)
        self._wl.append(client_fd)


class WebSocket_Simple_Server(WebSocket_Server_Base):
    
    def __init__(self, host, port):
        super(WebSocket_Simple_Server, self).__init__(host, port)


    def _frame_distribute(self, socket_fd, receive_frame):
        try:
            self._client_list[socket_fd].distribute(receive_frame)
        except exceptions.ConnectCLosed:
            self._close_fd(socket_fd)


    def _send_frame(self, socket_fd, send_frame):
        if isinstance(send_frame, frame.Frame_Base):
            socket_fd.send(send_frame.pack())
        socket_fd.send(send_frame)



def create_websocket_server(host = 'localhost', port = 8999, *, debug = False, logging_level = logging.INFO):
    utils.logger_init(logging_level)

    return WebSocket_Simple_Server(host, port)


def create_websocket_event_server():
    pass

