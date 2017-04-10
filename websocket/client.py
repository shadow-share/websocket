#!/usr/bin/env python3
#
# Copyright (C) 2017 ShadowMan
#


# Sec-WebSocket-Protocol - sub-protocol selector
#
# Sec-WebSocket-Extensions - list of extensions support by the client
#

# the default for "ws" is port 80, while the default for "wss" is port 443.
#
# ws-URI = "ws:" "//" host [ ":" port ] path [ "?" query ]
# wss-URI = "wss:" "//" host [ ":" port ] path [ "?" query ]
#

# The request MUST contain a |Host| header field whose value
# contains /host/ plus optionally ":" followed by /port/ (when not
# using the default port).

# The request MUST contain an |Upgrade| header field whose value
# MUST include the "websocket" keyword.

# The request MUST contain a |Connection| header field whose value
# MUST include the "Upgrade" token.

# The request MUST include a header field with the name
# |Sec-WebSocket-Key|

# The request MUST include a header field with the name |Origin|
# [RFC6454] if the request is coming from a browser client. If
# the connection is from a non-browser client, the request MAY
# include this header field if the semantics of that client match
# the use-case described here for browser clients. The value of
# this header field is the ASCII serialization of origin of the
# context in which the code establishing the connection is
# running.

# The request MUST include a header field with the name
# |Sec-WebSocket-Version|.  The value of this header field MUST be
# 13.

# The request MAY include a header field with the name
# |Sec-WebSocket-Protocol|.  If present, this value indicates one
# or more comma-separated subprotocol the client wishes to speak,
# ordered by preference.

# The request MAY include a header field with the name
# |Sec-WebSocket-Extensions|.  If present, this value indicates
# the protocol-level extension(s) the client wishes to speak.  The
# interpretation and format of this header field is described in
# Section 9.1.

# The request MAY include any other header fields, for example,
# cookies [RFC6265] and/or authentication-related header fields
# such as the |Authorization| header field [RFC2616], which are
# processed according to documents that define them.


# If the status code received from the server is not 101, the
# client handles the response per HTTP [RFC2616] procedures.

# If the response lacks an |Upgrade| header field or the |Upgrade|
# header field contains a value that is not an ASCII case-
# insensitive match for the value "websocket", the client MUST
# _Fail the WebSocket Connection_.

# If the response lacks a |Connection| header field or the
# |Connection| header field doesn't contain a token that is an
# ASCII case-insensitive match for the value "Upgrade", the client
# MUST _Fail the WebSocket Connection_.

# If the response lacks a |Sec-WebSocket-Accept| header field or
# the |Sec-WebSocket-Accept| contains a value other than the
# base64-encoded SHA-1 of the concatenation of the |Sec-WebSocket-
# Key| (as a string, not base64-decoded) with the string "258EAFA5-
# E914-47DA-95CA-C5AB0DC85B11" but ignoring any leading and
# trailing whitespace, the client MUST _Fail the WebSocket
# Connection_.

# If the response includes a |Sec-WebSocket-Extensions| header
# field and this header field indicates the use of an extension
# that was not present in the client's handshake (the server has
# indicated an extension not requested by the client), the client
# MUST _Fail the WebSocket Connection_.

# If the response includes a |Sec-WebSocket-Protocol| header field
# and this header field indicates the use of a subprotocol that was
# not present in the client's handshake (the server has indicated a
# subprotocol not requested by the client), the client MUST _Fail
# the WebSocket Connection_.

# Optionally, an |Origin| header field.
# This header field is sent by all browser clients.
# A connection attempt lacking this header field SHOULD NOT be
# interpreted as coming from a browser client.
import contextlib

class WebSocketClient(object):

    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type and exc_tb:
            raise exc_val

    @contextlib.contextmanager
    def cursor(self):
        pass

def create_websocket_client(host, port, debug=False):
    pass

