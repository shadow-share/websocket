#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#
import abc
import socket
import queue
from websocket import http, websocket_utils, frame, exceptions


class Distributer(object):

    def __init__(self, socket_fd, send_function, on_handshake, on_message, on_close, on_error):
        # Client socket file descriptor
        if not isinstance(socket_fd, socket.socket):
            raise TypeError('socket file descriptor must be socket.socket type')
        self._socket_fd = socket_fd
        # On handshake execute
        if not callable(on_handshake):
            raise TypeError('handshake handler must be callable')
        self._handshake_handler = on_handshake
        # On receive message execute
        if not callable(on_message):
            raise TypeError('message handler must be callable')
        self._message_handler = on_message
        # On error occurs execute
        if not callable(on_error):
            raise TypeError('error handler must be callable')
        self._error_handler = on_error
        # On receive/send close-frame execute
        if not callable(on_close):
            raise TypeError('close handler must be callable')
        self._close_handler = on_close
        # write queue
        if not callable(send_function):
            raise TypeError('send method must be callable')
        self._send = send_function
        # http request reference, using for header-fields check
        self._http_request = None
        # Accept http-handshake
        self._accept_request()


    def distribute(self, receive_frame):
        if receive_frame.frame_type in (frame.Text_Frame, frame.Binary_Frame):
            response_frame = self._message_handler(receive_frame.payload_data)
            if not isinstance(response_frame.message, frame.Frame_Base):
                raise TypeError('message handler return type must be a Frame')
            self._send(response_frame.message.pack())
        else:
            if receive_frame.flag_opcode is 0x8:
                self._on_receive_close_frame(receive_frame)
            else:
                print(receive_frame)


    def get_http_request(self):
        return self._http_request


    def _accept_request(self):
        self._receive_buffer = b''
        while True:
            data = self._socket_fd.recv(4096)
            if data:
                self._receive_buffer += data
                if b'\r\n\r\n' in self._receive_buffer:
                    break
        http_request = http.factory(self._receive_buffer)
        self._http_request = http_request
        ws_key = http_request[b'Sec-WebSocket-Key']

        http_response = http.HttpResponse(101,
            *http.create_header_fields(
                (b'Upgrade', b'websocket'),
                (b'Connection', b'Upgrade'),
                (b'Sec-WebSocket-Accept', websocket_utils.ws_accept_key(ws_key.value))
            ))

        self._handshake_handler(self._socket_fd.getsockname())
        self._send(http_response.pack())


    def _ws_send_ping(self, extra_data = None):
        self._send(frame.generate_ping_frame(False).pack())


    def _ws_send_pong(self, extra_data = None):
        self._send(frame.generate_pong_frame(False).pack())


    def _on_receive_ping(self, ping_frame):
        self._ws_send_pong()


    def _on_receive_close_frame(self, close_frame):
        self._close_handler(close_frame.payload_data if close_frame.payload_data else None)
        raise exceptions.ConnectCLosed

