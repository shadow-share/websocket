#!/usr/bin/env python3
#
# Copyright (C) 2017 ShadowMan
#
from websocket import utils

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

class WebSocket_Client(object):
    def __init__(self):
        pass
