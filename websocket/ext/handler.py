#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#
import abc
import socket


class WebSocketHandlerProtocol(object, metaclass=abc.ABCMeta):

    def __init__(self, socket_fd: socket.socket):
        self._socket_fd = socket_fd

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

    def broadcast(self, message):
        pass