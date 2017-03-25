#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#
from websocket.controller import base_controller

class EventController(base_controller.BaseController):

    def __init__(self, socket_fd, output, connect, message, close, error):
        super(EventController, self).__init__(
            socket_fd, output, connect, message, close, error)


    def _before_message_handler(self, payload_data):
        pass


    def _after_message_handler(self, response):
        pass

