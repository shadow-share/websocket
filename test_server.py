# -*- coding: utf-8 -*-
#!/usr/bin/env python
#
# Copyright (C) 2016 ShadowMan
#
import socket

# A single-frame unmasked text message
unmasked_text_frame = b'\x81\x05\x48\x65\x6c\x6c\x6f'
# A single-frame masked text message
masked_text_frame = b'\x81\x85\x37\xfa\x21\x3d\x7f\x9f\x4d\x51\x58'
# A fragmented unmasked text message
unmasked_fragment_text_frame_0 = b'\x01\x03\x48\x65\x6c'
unmasked_fragment_text_frame_1 = b'\x80\x02\x6c\x6f'
# Unmasked Ping request
unmasked_ping_frame = b'\x89\x05\x48\x65\x6c\x6c\x6f'
# 256 bytes binary message in a single unmasked frame
unmasked_binary_256B_frame = b'\x82\x7E\x01\x00' + (b'\x00' * 256)
# 64KiB binary message in a single unmasked frame
unmasked_binary_64KB_frame = b'\x82\x7F\x00\x00\x00\x00\x00\x01\x00\x00' + (b'\x00' * 64 * 1024)


def create_socket(host, port):
    fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    fd.connect((host, port))

    return fd

s = create_socket('localhost', 8999)
s.send(unmasked_binary_64KB_frame)
