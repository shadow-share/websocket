#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#
from websocket.net import http_message
from websocket.utils import logger


class HttpHeaderVerifier(object):

    def __init__(self):
        self._protocol_version = [ (13, lambda _: None) ]


    def verify(self, http_request):
        self._http_request = http_request


    def register_new_protocol_version(self, protocol_version):
        self._protocol_version.append(( int(protocol_version), lambda _: None))


    def _check_http_request_lead(self):
        if self._http_request.http_version != http_message.HTTP_VERSION_1_1:
            logger.error('websocket request muse be HTTP/1.1 or higher')
        if self._http_request.method != http_message.HTTP_METHOD_GET:
            logger.error('websocket request is not GET method')


    def _check_host(self):
        if not self._http_request['Host']:
            logger.error('loss Host field')
            # TODO, custom defined host verify


    # def _check_ws_header_fields(self):
    #     # An |Upgrade| header field containing the value "websocket",
    #     # treated as an ASCII case-insensitive value.
    #     if not utils.http_header_compare(self._http_request, 'Upgrade',
    #                                      'websocket'):
    #         utils.error_msg('http request miss Upgrade field')
    #     # A |Connection| header field that includes the token "Upgrade",
    #     # treated as an ASCII case-insensitive value.
    #     if not utils.http_header_compare(self._http_request, 'Connection',
    #                                      'Upgrade'):
    #         utils.error_msg('http request miss Upgrade field')
    #     # A |Sec-WebSocket-Key| header field with a base64-encoded (see
    #     # Section 4 of [RFC4648]) value that, when decoded, is 16 bytes in
    #     # length.
    #     key = self._http_request['Sec-WebSocket-Key']
    #     if key is None or not websocket_utils.ws_check_key_length(key.value):
    #         utils.error_msg('Sec-WebSocket-Key field invalid or miss')
    #     # A |Sec-WebSocket-Version| header field, with a value of 13.
    #     # TODO. register a new websocket version
    #     if not utils.http_header_compare(self._http_request,
    #                                      'Sec-WebSocket-Version', '13'):
    #         utils.error_msg('websocket version invalid')
    #     # Optionally, an |Origin| header field.  This header field is sent
    #     # by all browser clients.  A connection attempt lacking this
    #     # header field SHOULD NOT be interpreted as coming from a browser
    #     # client.
