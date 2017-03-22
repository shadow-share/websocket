#!/usr/bin/env python
#
# Copyright (C) 2017
#
from websocket.controller import base_controller

class PlainController(base_controller.BaseController):
    
    def __init__(self, socket_fd, output, on_connect, on_message, on_close, on_error):
        super(PlainController, self).__init__(socket_fd, output, on_connect, on_message, on_close, on_error)
