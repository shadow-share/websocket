#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#
import abc

class WebSocket_Handler(object, metaclass = abc.ABCMeta):

    def __init__(self):
        pass

    @abc.abstractclassmethod
    def on_connect(self, socket_name):
        pass


    @abc.abstractclassmethod
    def on_message(self, message):
        pass


    @abc.abstractclassmethod
    def on_close(self, socket_name):
        pass


    @abc.abstractclassmethod
    def on_error(self, error_reason):
        pass


