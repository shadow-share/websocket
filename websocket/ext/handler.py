#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#
import abc

class WebSocketHandlerProtocol(object, metaclass = abc.ABCMeta):

    def __init__(self):
        pass


    @abc.abstractclassmethod
    def on_connect(self, socket_name):
        pass


    @abc.abstractclassmethod
    def on_message(self, message):
        pass


    @abc.abstractclassmethod
    def on_close(self, code, reason):
        pass


    @abc.abstractclassmethod
    def on_error(self, code, reason):
        pass


    def export(self):
        return (self.on_connect, self.on_message, self.on_close, self.on_error)

