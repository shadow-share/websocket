#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#
import base64
import hashlib
from websocket.utils import generic

# GUID String
_const_guid_string = b'258EAFA5-E914-47DA-95CA-C5AB0DC85B11'

# The server has to take the value("Sec-WebSocket-Key"
# field) and concatenate this with the GUID
# "258EAFA5-E914-47DA-95CA-C5AB0DC85B11". A SHA-1 hash
# (160 bits), base64-encode, of this concatenation is
# the returned in the server's handshake
#
# base64-encode(SHA1(key + GUID))
def ws_accept_key(key):
    key = generic.to_bytes(key)
    hash_sha1 = hashlib.sha1(key + _const_guid_string)
    hash_sha1_rst = hash_sha1.digest()

    return base64.b64encode(hash_sha1_rst)


# The value of this header field MUST be a nonce consisting
# of a randomly selected 16-byte value that has been
# base64-encoded. The nonce MUST be selected randomly for
# each connection.
def ws_generate_key():
    random_16byte_string = generic.random_bytes_string(16)
    return base64.b64encode(random_16byte_string)


# A |Sec-WebSocket-Key| header field with a base64-encoded
# value that, when decoded, is 16 bytes in length.
def ws_check_key_length(key):
    if isinstance(key, (str, bytes)):
        return generic.base64_decode_length(key) is 16
    raise KeyError('the key must be str or bytes')

# All frames sent from the client to the server are masked by a
# 32-bit value that is contained within the frame.
def ws_generate_frame_mask_key():
    # 0x00 - 0xFF = 1byte(8 bit)
    return generic.random_bytes_string(4, start = 0x00, stop = 0xff)

