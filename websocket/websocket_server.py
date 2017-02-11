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

class Version_Handler_Interface(metaclass = abc.ABCMeta):
    def __init__(self):
        pass

    @abc.abstractclassmethod
    def checkout(self):
        pass

class WebSocket_Server_Base(metaclass = abc.ABCMeta):
    def __init__(self):
        self.__version_list = []
        self.__protocol_list = []

    def run(self, port = 8090, hostname = 'localhost', debug = False):
        pass

    def run_with_handler(self):
        pass

    def register_version(self, version, handler):
        pass

    def register_protocol(self, protocol_name, handler):
        pass

    def send_message(self):
        pass

class WebSocket_Server_Params_Checker_Mixin(WebSocket_Server_Base):
    def _from_header_fields_get(self, key):
        pass

    def _check_ws_key_length(self):
        ws_key = self._from_header_fields_get('Sec-WebSocket-Key')
        return utils.ws_check_key_length(ws_key)

    def _check_ws_version_valid(self):
        ws_version = self._from_header_fields_get('Sec-WebSocket-Version')
        return ws_version in self.__version_list

    def _check_ws_protocol_valid(self):
        pass

    def _check_ws_other_params(self):
        pass

class WebSocket_Plain_Server(WebSocket_Server_Base):
    pass

class WebSocket_Event_Server(WebSocket_Server_Base):
    pass

def create_ws_server():
    pass
