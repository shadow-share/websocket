# !/usr/bin/env python3
#
# Copyright (C) 2017 ShadowMan
#
import random
import socket
import websocket
from websocket.ext import handler

ws_server = websocket.create_websocket_server('0.0.0.0', port=8999, debug=False)


@ws_server.register_default_handler
class IndexHandler(handler.WebSocketHandlerProtocol):
    def __init__(self, socket_fd):
        handler.WebSocketHandlerProtocol.__init__(self, socket_fd)

    def on_connect(self):
        websocket.logger.info('client({}:{}) connected'.format(
            *self._socket_name))

    def on_message(self, message):
        websocket.logger.info('client({}:{}) receive message `{}`'.format(
            *self._socket_name, message.decode('utf-8')))
        if random.randint(0, 100) < 5:
            raise Exception('test close connection')
        return websocket.TextMessage('Hello World')

    def on_close(self, code, reason):
        websocket.logger.info('client({}:{}) closed {}:{}'.format(
            *self._socket_name, code, reason
        ))

    def on_error(self, code, reason):
        websocket.logger.warning('client({}:{}) error occurs'.format(
            *self._socket_name
        ))


@ws_server.register_handler('/chat')
class ChatHandler(handler.WebSocketHandlerProtocol):
    def __init__(self, socket_fd: socket.socket):
        handler.WebSocketHandlerProtocol.__init__(self, socket_fd)

    def on_connect(self):
        return ws_server.broadcast(websocket.TextMessage(
            'Welcome {}:{} join chat'.format(*self._socket_name)), True)

    def on_message(self, message):
        return ws_server.broadcast(websocket.TextMessage(message))

    def on_close(self, code, reason):
        return ws_server.broadcast(websocket.TextMessage(
            '{} exit chat room'.format(self._socket_name)))

    def on_error(self, code, reason):
        websocket.logger.warning('client({}:{}) error occurs'.format(
            *self._socket_name))

ws_server.run_forever()
