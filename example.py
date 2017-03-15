#!/usr/bin/env python3
#
# Copyright (C) 2017 ShadowMan
#
import logging
from websocket import websocket_server, frame, websocket_handler


class Simple_Handler(websocket_handler.WebSocket_Handler):

    def on_connect(self, socket_name):
        logging.info('Client {}:{} Connected'.format(*socket_name))

    def on_message(self, message):
        return frame.FileTextMessage(message)

    def on_close(self, close_reason):
        pass

    def on_error(self, socket_name):
        pass

ws_server = websocket_server.create_websocket_server(host = 'localhost', port = 8999)

ws_server.set_handler(Simple_Handler())
ws_server.run_forever()
