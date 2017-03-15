#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#
import abc
import socket
import queue
import logging
from websocket import http, websocket_utils, frame, exceptions, utils


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
            try:
                response_frame = self._message_handler(receive_frame.payload_data)
                if response_frame and not isinstance(response_frame.message, frame.Frame_Base):
                    raise TypeError('message handler return type must be a Frame')
                self._send(response_frame.message.pack())
            except Exception as e:
                logging.error(e)
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
        self._http_request_checker()

        ws_key = http_request[b'Sec-WebSocket-Key']
        http_response = http.HttpResponse(101,
            *http.create_header_fields(
                (b'Upgrade', b'websocket'),
                (b'Connection', b'Upgrade'),
                (b'Sec-WebSocket-Accept', websocket_utils.ws_accept_key(ws_key.value))
            ))

        self._handshake_handler(self._socket_fd.getpeername())
        self._send(http_response.pack())


    def _http_request_checker(self):
        self._check_http_request_line()
        self._check_host()
        # self._check_ws_header_fields()


    def _check_http_request_line(self):
        # An HTTP/1.1 or higher GET request, including a "Request-URI"
        if not (self._http_request.http_version == http.HTTP_VERSION_1_1):
            self._send(frame.generate_close_frame(False, extra_data = b''))
            raise exceptions.RequestError('request method muse be HTTP/1.1')
        if not (self._http_request.method == http.HTTP_METHOD_GET):
            self._send(frame.generate_close_frame(False, extra_data = b''))
            raise exceptions.RequestError('request method muse be HTTP/1.1')


    def _check_host(self):
        # A |Host| header field containing the server's authority.
        if not self._http_request['Host']:
            self._send(frame.generate_close_frame(False, extra_data = b''))
            raise exceptions.RequestError('Host field not in http request header')
            # TODO, custom defined host verify


    def _check_ws_header_fields(self):
        # An |Upgrade| header field containing the value "websocket",
        # treated as an ASCII case-insensitive value.
        if not utils.http_header_compare(self._http_request, 'Upgrade', 'websocket'):
            self._send(frame.generate_close_frame(False, extra_data = b''))
            raise exceptions.RequestError('http request miss Upgrade field')
        # A |Connection| header field that includes the token "Upgrade",
        # treated as an ASCII case-insensitive value.
        if not utils.http_header_compare(self._http_request, 'Connection', 'Upgrade'):
            self._send(frame.generate_close_frame(False, extra_data = b''))
            raise exceptions.RequestError('http request miss Upgrade field')
        # A |Sec-WebSocket-Key| header field with a base64-encoded (see
        # Section 4 of [RFC4648]) value that, when decoded, is 16 bytes in
        # length.
        key = self._http_request['Sec-WebSocket-Key']
        if key is None or not websocket_utils.ws_check_key_length(key.value):
            self._send(frame.generate_close_frame(False, extra_data = b''))
            raise exceptions.RequestError('Sec-WebSocket-Key field invalid or miss')
        # A |Sec-WebSocket-Version| header field, with a value of 13.
        # TODO. register a new websocket version
        if not utils.http_header_compare(self._http_request, 'Sec-WebSocket-Version', '13'):
            self._send(frame.generate_close_frame(False, extra_data = b''))
            raise exceptions.RequestError('websocket version invalid')


    def _check_origin(self):
        pass


    def _ws_send_ping(self, extra_data = None):
        self._send(frame.generate_ping_frame(False).pack())


    def _ws_send_pong(self, extra_data = None):
        self._send(frame.generate_pong_frame(False).pack())


    def _on_receive_ping(self, ping_frame):
        self._ws_send_pong()


    def _on_receive_close_frame(self, close_frame):
        self._close_handler(close_frame.payload_data if close_frame.payload_data else None)
        raise exceptions.ConnectCLosed

