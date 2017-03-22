#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#
import abc
from websocket.net import tcp_stream, http_message, ws_frame
from websocket.utils import (
    logger, exceptions, ws_utils
)


# TODO modify this
class BaseController(tcp_stream.TCPStream, metaclass = abc.ABCMeta):

    def __init__(self, socket_fd, output, on_connect, on_message, on_close, on_error):
        # TCP stream buffer
        super(BaseController, self).__init__(socket_fd)
        # initialize all event handler
        self._init_handler(on_connect, on_message, on_close, on_error)
        # output package method
        if not callable(output):
            raise TypeError('output method must be callable')
        self._output = output
        # wait http-handshake complete
        self._on_receive_ready = self._accept_http_handshake
        # verify http-header-fields tools TODO
        # self._http_verifier = HttpHeaderVerifier()
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
        super(BaseController, self).ready_receive()
        # on receive ready call
        self._on_receive_ready()


    def _init_handler(self, connect, message, close, error):
        for var_name, var_val in locals().items():
            if var_name != 'self' and not callable(var_val):
                raise TypeError('{} handler must be callable'.format(var_name))
        self._handlers = dict(locals())


    def _accept_http_handshake(self):
        header_pos = self.find_buffer(b'\r\n\r\n')
        if header_pos is -1:
            return
        http_request = http_message.factory(self.feed_buffer(header_pos))
        # TODO. chunk header-field
        if 'Content-Length' in http_request:
            print('have payload', http_request['Content-Length'].value)
            # drop payload data
            # TODO. payload data send to connect handler
            self.feed_buffer(http_request['Content-Length'].value)
        self._http_request = http_request
        # self._http_request_checker()

        ws_key = http_request[b'Sec-WebSocket-Key']
        http_response = http_message.HttpResponse(101, *http_message.create_header_fields(
            (b'Upgrade', b'websocket'),
            (b'Connection', b'Upgrade'),
            (b'Sec-WebSocket-Accept', ws_utils.ws_accept_key(ws_key.value))
        ))
        self._handlers['connect'](self._socket_fd.getpeername())
        self._output(http_response)
        self._on_receive_ready = self._distribute_frame


    def _distribute_frame(self):
        frame_header = self.peek_buffer(10)
        try:
            frame_length = ws_frame.parse_frame_length(frame_header)
        except Exception:
            raise

        if self.buffer_length() < frame_length:
            return
        complete_frame = ws_frame.WebSocketFrame(self.feed_buffer(frame_length))
        self._opcode_handlers.get(complete_frame.flag_opcode)(complete_frame)


    def _valid_message(self, complete_frame):
        try:
            response = self._handlers['message'](complete_frame.payload_data)
            if response is None:
                logger.warning('handler is ignore one message')
                return
            elif hasattr(response, 'pack'):
                self._output(response)
            elif hasattr(response, 'generate_frame'):
                self._output(response.generate_frame)
            else:
                raise TypeError('response must be pack-like object')
        except Exception as e:
            # error occurs but handler not solution
            logger.error('Client({}:{}) Error Occurs({})'.format(
                *self._socket_fd.getpeername(), str(e)))
            raise exceptions.ConnectClosed((1002, str(e)))


    def _recv_close(self, complete_frame):
        self._handlers['close'](complete_frame.payload_data)
        # If an endpoint receives a Close frame and did not previously send
        # a Close frame, the endpoint MUST send a Close frame in response
        raise exceptions.ConnectClosed((1000, ''))


    def _recv_ping(self, complete_frame):
        logger.debug('Client({}:{}) receive ping frame'.format(
            *self._socket_fd.getpeername()))
        self._output(ws_frame.generate_pong_frame())


    def _recv_pong(self, complete_frame):
        logger.debug('Client({}:{}) receive pong frame'.format(
            *self._socket_fd.getpeername()))
