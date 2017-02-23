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

serv.bind(('127.0.0.1', 8999))
serv.listen(4)

while (True):
    cli, addr = serv.accept()
    print(cli)
    frame = frame.Frame_Parser(cli)
    print(frame.flag_fin, frame.flag_rsv1, frame.flag_rsv2, frame.flag_rsv3, frame.flag_opcode)
    print(frame._mask_flag, frame.payload_data_length)
    print(frame.mask_key)
    print(frame.payload_data)
    cli.close()
    break
