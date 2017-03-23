# !/usr/bin/env python3
#
# Copyright (C) 2017 ShadowMan
#
import random
import websocket
from websocket.ext import handler


class SimpleHandler(handler.WebSocketHandlerProtocol):
    
    def __init__(self):
        self._socket_name = None
        super(SimpleHandler, self).__init__()

    def on_connect(self, socket_name):
        self._socket_name = socket_name
        websocket.logger.info('client({}:{}) connected'.format(*socket_name))

    def on_message(self, message):
        websocket.logger.info('client({}:{}) send message `{}`'.format(
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


ws_server = websocket.create_websocket_server('0.0.0.0', port = 8999, debug = True)


ws_server.set_handler(SimpleHandler())
ws_server.run_forever()
