#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#
import abc
from websocket.ext import frame_verifier
from websocket.net import tcp_stream, ws_frame
from websocket.utils import (
    logger, exceptions
)


class BaseController(object, metaclass=abc.ABCMeta):

    def __init__(self, stream: tcp_stream.TCPStream, output, handler):
        # socket file descriptor
        self._socket_fd = stream.get_socket_fd()
        # TCP stream buffer
        self._tcp_stream = stream
        # websocket event handler
        self._handlers = handler  # WebSocketHandlerProtocol
        # output package method
        if not callable(output):
            raise TypeError('output method must be callable')
        self._output = output
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
        frame_header = self._tcp_stream.peek_buffer(10)
        try:
            if len(frame_header) < 2:
                return
            frame_length = ws_frame.parse_frame_length(frame_header)
        except Exception:
            raise

        if self._tcp_stream.buffer_length() < frame_length:
            return
        frame = ws_frame.WebSocketFrame(
            self._tcp_stream.feed_buffer(frame_length))
        if not frame_verifier.verify_frame(self._socket_fd, frame):
            logger.error('Receive Client Frame Format Invalid {}'.format(frame))
        logger.debug('Receive Client({}:{}) frame: {}'.format(
            *self._socket_fd.getpeername(), frame))
        self._opcode_handlers.get(frame.flag_opcode)(frame)

    # opcode =data_pack:ws_frame.FrameBase 1 or opcode = 2
    # TODO. opcode = 0
    def _valid_message(self, complete_frame: ws_frame.FrameBase):
        try:
            response = self._handlers.on_message(
                self._before_message_handler(complete_frame.payload_data))
            response = self._after_message_handler(response)
            if response is True:
                return
            elif response is None:
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
        self._handlers.on_close(code, reason)
        # If an endpoint receives a Close frame and did not previously send
        # a Close frame, the endpoint MUST send a Close frame in response
        raise exceptions.ConnectClosed((1000, ''))

    def _recv_ping(self, complete_frame):
        logger.debug('Client({}:{}) receive ping frame'.format(
            *self._socket_fd.getpeername()))
        self._output(ws_frame.generate_pong_frame(
            extra_data=complete_frame.payload_data))

    def _recv_pong(self, complete_frame):
        logger.debug('Client({}:{}) receive pong frame({})'.format(
            *self._socket_fd.getpeername(), complete_frame.payload_data))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type or exc_tb:
            raise exc_val
