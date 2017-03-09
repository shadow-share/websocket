#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#
import abc
import socket
import queue
from websocket import http, utils, websocket_utils


class Distributer(object):

    def __init__(self, socket_fd):
        # Client socket file descriptor
        self._socket_fd = socket_fd
        # Receive data buffer
        self._receive_buffer = None
        # Send data buffer
        self._send_buffer = None
        # On handshake execute
        self._handshake_handler = None
        # On receive message execute
        self._message_handler = None
        # On error occurs execute
        self._error_handler = None
        # On receive/send close-frame execute
        self._close_handler = None
        # Accept http-handshake
        self._accept_request()


    def send_message(self):
        pass


    def receive_message(self):
        pass


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

