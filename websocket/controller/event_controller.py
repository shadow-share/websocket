#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#
from websocket.controller import base_controller

class EventController(base_controller.BaseController):

    def __init__(self):
        super(EventController, self).__init__()
