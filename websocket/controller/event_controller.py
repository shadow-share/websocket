#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#
from websocket.controller import base_controller


class EventController(base_controller.BaseController):

    def __init__(self, stream, output, handler):
        super(EventController, self).__init__(stream, output, handler)

    def _before_message_handler(self, payload_data):
        pass

    def _after_message_handler(self, response):
        pass
