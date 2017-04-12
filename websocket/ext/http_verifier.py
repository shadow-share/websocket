#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#
from websocket.net import http_message
from websocket.utils import (
    logger, generic, exceptions, ws_utils
)


_enable_http_verifier = True


def enable():
    global _enable_http_verifier
    _enable_http_verifier = True


def disable():
    global _enable_http_verifier
    _enable_http_verifier = False


_server_name = tuple()


def set_server_name(server_name, *, port=80):
    global _server_name
    _server_name = (server_name, port)


_origin_value = None


def verify_origin(origin_value):
    global _origin_value
    _origin_value = generic.to_string(origin_value)


class HttpHandshakeVerifier(object):

    def __init__(self, client_name, request):
        super(HttpHandshakeVerifier, self).__init__()
        self._request = request
        self._client_name = client_name
        self._verify_websocket_options()

    def verify_host(self):
        if 'Host' not in self._request.header:
            self._raise_error_message(
                '{} loss `Host` option'.format(self._client_name))
        if not _server_name:
            raise exceptions.FatalError('Server Internal Error, Please report')
        if _server_name[0] is True:
            return True

        _host = self._request.header.get_value('Host', value_type=str)
        if _server_name[1] is 80:
            return _host == _server_name[0]
        return _host == ':'.join(
            map(lambda x: generic.to_string(x), _server_name))

    def verify_origin(self):
        global _origin_value
        if _origin_value is None:
            return True
        return self._compare_option('Origin', _origin_value, False)

    @staticmethod
    def verify_sec_websocket_extensions():
        return []

    def _verify_websocket_options(self):
        # An |Upgrade| header field containing the value "websocket",
        # treated as an ASCII case-insensitive value.
        if not self._compare_option('upgrade', 'websocket', False):
            raise exceptions.HttpVerifierError(
                'Client({}) `Upgrade` is not `websocket`'.format(
                    self._client_name))
        # A |Connection| header field that includes the token "Upgrade",
        # treated as an ASCII case-insensitive value.
        if not self._compare_option('Connection', 'Upgrade'):
            raise exceptions.HttpVerifierError(
                'Client({}) `Connection` is not `Upgrade`'.format(
                    self._client_name))
        # A |Sec-WebSocket-Key| header field with a base64-encoded value that,
        # when decoded, is 16 bytes in length.
        _sec_websocket_key = self._request.header.get_value('Sec-WebSocket-Key')
        if not ws_utils.ws_check_key_length(_sec_websocket_key):
            raise exceptions.HttpVerifierError(
                'Client({}) `Sec-WebSocket-Key` is invalid'.format(
                    self._client_name))
        # A |Sec-WebSocket-Version| header field, with a value of 13.
        if not self._compare_option('Sec-WebSocket-Version', '13', False):
            raise exceptions.HttpVerifierError(
                'Client({}) `Sec-WebSocket-Version` is not `13`'.format(
                    self._client_name))

    def _compare_option(self, option_name, except_value, case_insensitive=True):
        except_value = generic.to_string(except_value)
        if option_name not in self._request.header:
            self._raise_error_message(
                '{} loss `{}` option'.format(self._client_name, option_name))
        _value = self._request.header.get_value(option_name, value_type=str)
        if case_insensitive:
            return _value == except_value
        return _value.lower() == except_value.lower()

    @staticmethod
    def _raise_error_message(error_message):
        logger.error(error_message)
        raise exceptions.HttpVerifierError(error_message)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type and exc_tb:
            raise exc_val


def verify_request(client_name, request):
    if _enable_http_verifier is False:
        return True
    if not isinstance(request, http_message.HttpRequest):
        raise exceptions.raise_parameter_error(
            'request', http_message.HttpRequest, request)

    with HttpHandshakeVerifier(client_name, request) as verifier:
        # A |Host| header field containing the server's authority.
        if not verifier.verify_host():
            raise exceptions.HttpVerifierError(
                'Client({}) `Host` invalid'.format(client_name))
        # The |Origin| header field in the client's handshake indicates
        # the origin of the script establishing the connection. If the
        # server does not validate the origin, it will accept connections
        # from anywhere.  If the server does not wish to accept this
        # connection, it MUST return an appropriate HTTP error code
        # (e.g., 403 Forbidden) and abort the WebSocket handshake
        # described in this section.
        if not verifier.verify_origin():
            raise exceptions.HttpVerifierError(
                'Client({}) `Origin` invalid'.format(client_name))
        # Optionally, a |Sec-WebSocket-Extensions| header field, with a
        # list of values indicating which extensions the client would like
        # to speak.
        return verifier.verify_sec_websocket_extensions()
        # Unknown header fields are ignored
