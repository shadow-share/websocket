#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#
import abc
import socket
import queue
import logging
from websocket import http, websocket_utils, frame, exceptions, utils


class TCPStream(object):


    def __init__(self, socket_fd:socket.socket):
        # manager of socket file descriptor
        self._socket_fd = socket_fd # type: socket.socket
        # receive buffer
        self._receive_buffer = b'' # type: bytes


    def ready_receive(self):
        self._receive_buffer = self._receive_buffer + self._socket_feed(4096)


    def find_buffer(self, sub_content):
        sub_content = utils.to_bytes(sub_content)
        pos = self._receive_buffer.find(sub_content)
        if pos >= 0:
            pos += 4 + 1
        return pos


    def feed_buffer(self, stop = None, start = 0):
        if stop is None:
            stop = len(self._receive_buffer)
        else:
            stop = min(stop, len(self._receive_buffer))
        rst = self._receive_buffer[start:stop]
        self._receive_buffer = self._receive_buffer[stop:]
        return rst


    def peek_buffer(self, stop = None, start = 0):
        if stop is None:
            stop = len(self._receive_buffer)
        else:
            stop = min(stop, len(self._receive_buffer))
        return self._receive_buffer[start:stop]


    def buffer_length(self):
        return len(self._receive_buffer)


    def _socket_feed(self, buffer_size = 4096):
        try:
            return self._socket_fd.recv(buffer_size)
        except Exception:
            raise



class HttpHeaderVerifier(object):

    def __init__(self, http_request:http.HttpRequest):
        self._http_request = http_request


    @classmethod
    def factory(cls):
        pass


    def _check_http_request_lead(self):
        if self._http_request.http_version != http.HTTP_VERSION_1_1:
            utils.error_msg('websocket request muse be HTTP/1.1 or higher')
        if self._http_request.method != http.HTTP_METHOD_GET:
            utils.error_msg('websocket request is not GET method')

    def _check_host(self):
        if not self._http_request['Host']:
            utils.error_msg('loss Host field')
            # TODO, custom defined host verify

    def _check_ws_header_fields(self):
        # An |Upgrade| header field containing the value "websocket",
        # treated as an ASCII case-insensitive value.
        if not utils.http_header_compare(self._http_request, 'Upgrade',
                                         'websocket'):
            utils.error_msg('http request miss Upgrade field')
        # A |Connection| header field that includes the token "Upgrade",
        # treated as an ASCII case-insensitive value.
        if not utils.http_header_compare(self._http_request, 'Connection',
                                         'Upgrade'):
            utils.error_msg('http request miss Upgrade field')
        # A |Sec-WebSocket-Key| header field with a base64-encoded (see
        # Section 4 of [RFC4648]) value that, when decoded, is 16 bytes in
        # length.
        key = self._http_request['Sec-WebSocket-Key']
        if key is None or not websocket_utils.ws_check_key_length(key.value):
            utils.error_msg('Sec-WebSocket-Key field invalid or miss')
        # A |Sec-WebSocket-Version| header field, with a value of 13.
        # TODO. register a new websocket version
        if not utils.http_header_compare(self._http_request,
                                         'Sec-WebSocket-Version', '13'):
            utils.error_msg('websocket version invalid')
        # Optionally, an |Origin| header field.  This header field is sent
        # by all browser clients.  A connection attempt lacking this
        # header field SHOULD NOT be interpreted as coming from a browser
        # client.


class Distributer(TCPStream):

    def __init__(self, socket_fd, output, on_connect, on_message, on_close, on_error):
        # TCP stream buffer
        super(Distributer, self).__init__(socket_fd)
        # initialize all event handler
        self._init_handler(on_connect, on_message, on_close, on_error)
        # output package method
        if not callable(output):
            raise TypeError('output method must be callable')
        self._output = output
        # wait http-handshake complete
        self._on_receive_ready = self._accept_http_handshake
        # verify http-header-fields tools
        self._http_verifier = HttpHeaderVerifier()
        # opcode handler mapping
        self._opcode_handlers = {
            0x0: lambda f: print(f), 0x1: self._valid_message,
            0x2: self._valid_message, 0x3: lambda f: print(f),
            0x4: lambda f: print(f), 0x5: lambda f: print(f),
            0x6: lambda f: print(f), 0x7: lambda f: print(f),
            0x8: lambda f: print(f), 0x9: lambda f: print(f),
            0xA: lambda f: print(f), 0xB: lambda f: print(f),
            0xC: lambda f: print(f), 0xD: lambda f: print(f),
            0xE: lambda f: print(f), 0xF: lambda f: print(f),
        }


    def ready_receive(self):
        # feed all socket tcp buffer
        super(Distributer, self).ready_receive()
        # on receive ready call
        self._on_receive_ready()


    def _init_handler(self, connect, message, close, error):
        for var_name, var_val in locals().items():
            if var_name != 'self' and not callable(var_val):
                raise TypeError('{} handler must be callable'.format(var_name))
        self._handlers = dict(locals())


    def _accept_http_handshake(self):
        header_pos = self.find_buffer(b'\r\n\r\n')
        if not header_pos:
            return
        http_request = http.factory(self.feed_buffer(header_pos))
        # TODO. chunk header-field
        if 'Content-Length' in http_request:
            print('have payload', http_request['Content-Length'].value)
            # drop payload data
            # TODO. payload data send to connect handler
            self.feed_buffer(http_request['Content-Length'].value)
        self._http_request = http_request
        # self._http_request_checker()

        ws_key = http_request[b'Sec-WebSocket-Key']
        http_response = http.HttpResponse(101, *http.create_header_fields(
            (b'Upgrade', b'websocket'),
            (b'Connection', b'Upgrade'),
            (b'Sec-WebSocket-Accept', websocket_utils.ws_accept_key(ws_key.value))
        ))
        self._handlers['connect'](self._socket_fd.getpeername())
        self._output(http_response)
        self._on_receive_ready = self._distribute_frame


    def _distribute_frame(self):
        frame_header = self.peek_buffer(10)
        try:
            frame_length = frame.parse_frame_length(frame_header)
        except Exception:
            raise

        if self.buffer_length() < frame_length:
            return
        complete_frame = frame.WebSocketFrame(self.feed_buffer(frame_length))
        self._opcode_handlers.get(complete_frame.flag_opcode)(complete_frame)


    def _valid_message(self, complete_frame):
        try:
            response = self._handlers['message'](complete_frame.payload_data)
            if hasattr(response, 'pack'):
                self._output(response)
            elif hasattr(response, 'generate_frame'):
                self._output(response.generate_frame)
            else:
                raise TypeError('response must be pack-like object')
        except Exception as e:
            # error occurs but handler not solution
            utils.error_msg('Client({}:{}) Error Occurs({})'.format(
                *self._socket_fd.getpeername(), str(e)))
            raise exceptions.ConnectClosed((1002, str(e)))


    def _recv_close(self, complete_frame):
        self._handlers['close'](complete_frame.payload_data)
        # If an endpoint receives a Close frame and did not previously send
        # a Close frame, the endpoint MUST send a Close frame in response
        raise exceptions.ConnectClosed((1000, ''))


    def _recv_ping(self, complete_frame):
        utils.debug_msg('Client({}:{}) receive ping frame'.format(
            *self._socket_fd.getpeername()))
        self._output(frame.generate_pong_frame())


    def _recv_pong(self, complete_frame):
        utils.debug_msg('Client({}:{}) receive pong frame'.format(
            *self._socket_fd.getpeername()))
