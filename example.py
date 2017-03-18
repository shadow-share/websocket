# !/usr/bin/env python3
#
# Copyright (C) 2017 ShadowMan
#
from websocket import websocket_server, frame, websocket_handler, utils


class Simple_Handler(websocket_handler.WebSocket_Handler):

    def __init__(self):
        super(Simple_Handler, self).__init__()
        self._socket_name = None  # type: tuple

    def on_connect(self, socket_name):
        self._socket_name = socket_name
        utils.info_msg('Client {}:{} connected'.format(*socket_name))

    def on_message(self, message):
        try:
            return frame.FileTextMessage(message)
        except Exception as e:
            raise
            # return frame.TextMessage(str(e))

    def on_close(self, close_reason):
        utils.info_msg('Client {}:{} closed'.format(*self._socket_name))

    def on_error(self, socket_name):
        pass


ws_server = websocket_server.create_websocket_server(host = '0.0.0.0',
                                                     port = 8999, debug = True)
ws_server.set_handler(Simple_Handler())
ws_server.run_forever()
