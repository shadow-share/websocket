#!/usr/bin/env python3
#
# Copyright (C) 2017 ShadowMan
#
from websocket import websocket_server, frame


def on_connect(socket_name):
    print(socket_name)


def on_message(message):
    return frame.FileTextMessage(message)


def on_close(reason):
    print(reason)


def on_error():
    pass


ws_server = websocket_server.create_websocket_server(host = 'localhost', port = 8999)

ws_server.set_handler(on_connect, on_message, on_close, on_error)
ws_server.run_forever()
