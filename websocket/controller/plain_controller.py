#!/usr/bin/env python
#
# Copyright (C) 2017
#
from websocket.controller import base_controller


class PlainController(base_controller.BaseController):

    def __init__(self, stream, output, handler):
        super(PlainController, self).__init__(stream, output, handler)

    def _after_message_handler(self, response):
        return response

    def _before_message_handler(self, payload_data):
        return payload_data
