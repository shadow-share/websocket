#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#
import socket
from websocket.utils import generic


class TCPStream(object):

    def __init__(self, socket_fd: socket.socket):
        # manager of socket file descriptor
        self._socket_fd = socket_fd  # type: socket.socket
        # receive buffer
        self._receive_buffer = b''  # type: bytes

    def ready_receive(self):
        self._receive_buffer = self._receive_buffer + self._socket_feed(4096)

    def find_buffer(self, sub_content):
        sub_content = generic.to_bytes(sub_content)
        pos = self._receive_buffer.find(sub_content)
        if pos >= 0:
            pos += len(sub_content) + 1
        return pos

    def feed_buffer(self, stop=None, start=0):
        if stop is None:
            stop = len(self._receive_buffer)
        else:
            stop = min(stop, len(self._receive_buffer))
        rst = self._receive_buffer[start:stop]
        self._receive_buffer = self._receive_buffer[stop:]
        return rst

    def peek_buffer(self, stop=None, start=0):
        if stop is None:
            stop = len(self._receive_buffer)
        else:
            stop = min(stop, len(self._receive_buffer))
        return self._receive_buffer[start:stop]

    def buffer_length(self):
        return len(self._receive_buffer)

    def _socket_feed(self, buffer_size=4096):
        try:
            return self._socket_fd.recv(buffer_size)
        except Exception:
            raise

    def get_socket_fd(self):
        return self._socket_fd
