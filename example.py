#!/usr/bin/env python3
#
# Copyright (C) 2017 ShadowMan
#
import os
import sys
import random
import socket
import struct
from websocket import utils

key = utils.ws_generate_key()
accept = utils.ws_accept_key(key)
print(key, accept)

serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

serv.bind(('localhost', 8123))

serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)

serv.listen(10)

while (True):
    cli, addr = serv.accept()
    print(cli, addr)
    buf = cli.recv(4096)

    utils.http_header_parser(buf)

    print(buf)

    arr = buf.decode('utf-8').split('\r\n')
    arr = list(map(lambda x: tuple(x.split(': ')), arr))
    key = ''
    for t in arr:
        if len(t) == 1:
            continue
        k,v = t
        if k == 'Sec-WebSocket-Key':
            key = v
            break
    print(key)

    rst = utils.ws_accept_key(key)

    cli.send(b'HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: ' + rst + b'\r\n\r\n')
    cli.close()

