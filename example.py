#!/usr/bin/env python3
#
# Copyright (C) 2017 ShadowMan
#
from websocket import websocket_server

ws_server = websocket_server.create_websocket_server(host = 'localhost', port = 8999)

ws_server.run_forever()
