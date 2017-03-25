#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#
import abc
from websocket.net import tcp_stream, http_message, ws_frame, http_verifier
from websocket.utils import (
    logger, exceptions, ws_utils
)


# TODO modify this
class BaseController(object, metaclass = abc.ABCMeta):

    def __init__(self, socket_fd, output, connect, message, close, error):
        # socket file descriptor
        self._socket_fd = socket_fd
        # TCP stream buffer
        self._tcp_stream = tcp_stream.TCPStream(socket_fd)
        # websocket event handler
        self._handlers = dict()
        # output package method
        if not callable(output):
            raise TypeError('output method must be callable')
        self._output = output
        # wait http-handshake complete
        self._on_receive_ready = self._accept_http_handshake
        # verify http-header-fields tools TODO
        self._http_verifier = http_verifier.HttpHeaderVerifier()
        # opcode handler mapping
        self._opcode_handlers = {
            0x0: lambda f: print(f), 0x1: self._valid_message,
            0x2: self._valid_message, 0x3: lambda f: print(f),
            0x4: lambda f: print(f), 0x5: lambda f: print(f),
            0x6: lambda f: print(f), 0x7: lambda f: print(f),
            0x8: self._recv_close, 0x9: lambda f: print(f),
            0xA: lambda f: print(f), 0xB: lambda f: print(f),
            0xC: lambda f: print(f), 0xD: lambda f: print(f),
            0xE: lambda f: print(f), 0xF: lambda f: print(f),
        }


    def ready_receive(self):
        # feed all socket tcp buffer
        self._tcp_stream.ready_receive()
        # on receive ready call
        self._on_receive_ready()


    def init_handler(self, connect, message, close, error):
        for var_name, var_val in locals().items():
            if var_name != 'self' and not callable(var_val):
                raise TypeError('{} handler must be callable'.format(var_name))
            self._handlers[var_name] = var_val


    def _accept_http_handshake(self):
        pos = self._tcp_stream.find_buffer(b'\r\n\r\n')
        if pos is -1:
            return
        http_request = http_message.factory(self._tcp_stream.feed_buffer(pos))
        logger.debug('Request: {}'.format(repr(http_request)))
        # TODO. chunk header-field
        if 'Content-Length' in http_request:
            print('have any payload', http_request['Content-Length'].value)
            # drop payload data
            # TODO. payload data send to connect handler
            self._tcp_stream.feed_buffer(http_request['Content-Length'].value)
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
        frame_header = self._tcp_stream.peek_buffer(10)
        try:
            frame_length = ws_frame.parse_frame_length(frame_header)
        except Exception:
            raise

        if self._tcp_stream.buffer_length() < frame_length:
            return
        frame = ws_frame.WebSocketFrame(self._tcp_stream.feed_buffer(frame_length))
        logger.debug('Receive Client({}:{}) frame: {}'.format(
            *self._socket_fd.getpeername(), frame))
        self._opcode_handlers.get(frame.flag_opcode)(frame)

    # opcode =data_pack:ws_frame.FrameBase 1 or opcode = 2
    # TODO. opcode = 0
    def _valid_message(self, complete_frame:ws_frame.FrameBase):
        try:
            response = self._handlers['message'](
                self._before_message_handler(complete_frame.payload_data))
            response = self._after_message_handler(response)
            if response is None:
                logger.warning('message handler ignore from client message')
                return
            elif hasattr(response, 'pack'):
                self._output(response)
            elif hasattr(response, 'generate_frame'):
                self._output(response.generate_frame)
            else:
                raise exceptions.InvalidResponse('invalid response')
        except exceptions.InvalidResponse:
            logger.error('message handler return value is invalid response')
            raise
        except Exception as e:
            # error occurs but handler not solution
            logger.error('Client({}:{}) Error occurs({})'.format(
                *self._socket_fd.getpeername(), str(e)))
            raise exceptions.ConnectClosed((1002, str(e)))


    @abc.abstractclassmethod
    def _before_message_handler(self, payload_data):
        pass


    @abc.abstractclassmethod
    def _after_message_handler(self, response):
        pass


    def _recv_close(self, complete_frame):
        if len(complete_frame.payload_data) >= 2:
            code = complete_frame.payload_data[0:2]
            reason = complete_frame.payload_data[2:]
        else:
            code, reason = 1000, b''
        self._handlers['close'](code, reason)
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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type or exc_tb:
            raise exc_val
