#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#
import abc
import socket
from websocket import http, utils, websocket_utils


class Distributer(object):

    def __init__(self, socket_fd):
        self._socket_fd = socket_fd
        self._receive_buffer = None
        self._send_buffer = None
        self._handshake_handler = None
        self._message_handler = None
        self._error_handler = None
        self._close_handler = None

        self._accept_request()

    def distribute(self, frame):
        pass

    def _accept_request(self):
        self._receive_buffer = b''
        while True:
            data = self._socket_fd.recv(4096)
            if data:
                self._receive_buffer += data
                if b'\r\n\r\n' in self._receive_buffer:
                    break
        http_request = http.factory(self._receive_buffer)
        ws_key = http_request[b'Sec-WebSocket-Key']
        print(ws_key)

        http_response = http.HttpResponse(101,
            *http.create_header_fields(
                (b'Upgrade', b'websocket'),
                (b'Connection', b'Upgrade'),
                (b'Sec-WebSocket-Accept', websocket_utils.ws_accept_key(ws_key.value))
            )
        )
        print(http_response.pack())
        self._socket_fd.sendall(http_response.pack())

    def _ws_handshake(self):
        pass


