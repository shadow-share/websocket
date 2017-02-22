#!/usr/bin/env python3
#
# Copyright (C) 2017 ShadowMan
#
import os
import sys
import random
import socket
import struct
from websocket import utils, frame

serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

serv.bind(('127.0.0.1', 8909))
serv.listen(4)

while (True):
    cli, addr = serv.accept()
    print(cli)
    print(frame.receive_single_frame(cli))
    cli.close()
    break
