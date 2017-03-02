#!/usr/bin/env python3
#
# Copyright (C) 2017 ShadowMan
#

# An HTTP/1.1 or higher GET request, including a "Request-URI"

# A |Host| header field containing the server's authority.

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
from websocket import utils, frame


class WebSocket_Protocol(object, metaclass = abc.ABCMeta):

    def __init__(self):
        pass

    @abc.abstractclassmethod
    def on_connect(self):
        pass

    @abc.abstractclassmethod
    def on_message(self, message):
        pass

    @abc.abstractclassmethod
    def on_close(self):
        pass

    @abc.abstractclassmethod
    def on_error(self):
        pass

    def on_receive_frame(self, raw_frame):
        pass

class WebSocket_Server_Base(object, metaclass = abc.ABCMeta):

    def __init__(self, host, port):
        self._client_list = {}
        self._server_address = (host, port)

    def run_forever(self):
        self._server_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self._server_fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_fd.setblocking(False)

        self._server_fd.bind(self._server_address)
        self._server_fd.listen(16)
        self._select_loop()

    def _select_loop(self):
        self._rl, self._wl, self._xl = [ self._server_fd ], [], []

        while True:
            rl, wl, el = select.select(self._rl, self._wl, self._xl)

            self._read_list_handler(rl)
            self._write_list_handler(wl)
            self._error_list_handler(el)

    def _read_list_handler(self, rl):
        pass

    def _write_list_handler(self, wl):
        pass

    def _error_list_handler(self, el):
        pass

    def _accept_client(self):
        client_fd, client_address = self._server_fd.accept()

        self._rl.append(client_fd)
        self._wl.append(client_fd)


class WebSocket_Simple_Server(WebSocket_Server_Base):
    
    def __init__(self, host, port, *, handler):
        super(WebSocket_Simple_Server, self).__init__(host, port)

        if isinstance(handler, WebSocket_Protocol):
            self.on_connect(handler.on_connect)
            self.on_message(handler.on_message)
            self.on_close(handler.on_close)
            self.on_error(handler.on_error)

    def on_connect(self, handler):
        if callable(handler):
            handler()

    def on_message(self, handler):
        if callable(handler):
            handler()

    def on_close(self, handler):
        if callable(handler):
            handler()

    def on_error(self, handler):
        if callable(handler):
            handler()

    def set_interval(self, timeout, handler):
        pass

def create_websocket_server(host = 'localhost', port = 8999, debug = False):
    return WebSocket_Simple_Server(host, port)


def create_websocket_event_server():
    pass

