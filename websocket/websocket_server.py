#!/usr/bin/env python3
#
# Copyright (C) 2017 ShadowMan
#
import abc
import socket
from websocket import utils

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

class WebSocket_Server_Base(object, metaclass = abc.ABCMeta):

    def __init__(self):
        pass


def create_websocket_server():
    pass

def create_websocket_event_server():
    pass

