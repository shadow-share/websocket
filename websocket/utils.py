#!/usr/bin/env python3
#
# Copyright (C) 2017 ShadowMan
#
import base64
import hashlib
import random
from collections import namedtuple

# Http version 1.1
# The method of the request MUST be GET, and the HTTP version MUST
# be at least 1.1.
HTTP_VERSION_1_1 = '1.1'

# Response status code description
_response_status_code_description = {
    400: 'Bad Request',
    401: '',
    403: 'Forbidden',
    404: 'Not Found',
    426: 'Upgrade Required'
}

# Request line namedtuple
Request_Line = namedtuple('Request_Line', 'method path version')

# Header item namedtuple
Header_Field = namedtuple('Header_Item', 'key value')

# Request header namedtuple
Request_Header = namedtuple('Request_Header', 'lead fields')

# GUID
_const_guid_string = b'258EAFA5-E914-47DA-95CA-C5AB0DC85B11'

def to_string(byte_string, encoding = 'utf-8'):
    if not isinstance(byte_string, str):
        if hasattr(bytes, 'decode'):
            return byte_string.decode(encoding)
        else:
            raise KeyError('the byte_string has\'t decode method')
    else:
        return byte_string

def to_bytes(string, encoding = 'utf-8'):
    if not isinstance(string, bytes):
        if hasattr(string, 'encode'):
            return string.encode(encoding)
        else:
            raise KeyError('the string has\'t encode method')
    else:
        return string

def ws_accept_key(key):
    key = to_bytes(key)
    hash_sha1 = hashlib.sha1(key + _const_guid_string)
    hash_sha1_rst = hash_sha1.digest()

    return base64.b64encode(hash_sha1_rst)

# a nonce consisting of a randomly selected 16-byte value
# 1-byte(0 - 127), not 0 - 255
def _random_bytes_string(string_size, start = 0, stop = 0x7f, encoding = 'utf-8'):
    rst_string = b''
    for _ in range(string_size):
        rst_string += chr(random.randint(start, stop)).encode(encoding)
    return rst_string

# The value of this header field MUST be a
# nonce consisting of a randomly selected 16-byte value that has
# been base64-encoded (see Section 4 of [RFC4648]).  The nonce
# MUST be selected randomly for each connection.
def ws_generate_key():
    random_16byte_string = _random_bytes_string(16)
    return base64.b64encode(random_16byte_string)

# A |Sec-WebSocket-Key| header field with a base64-encoded
# value that, when decoded, is 16 bytes in length.
def ws_check_key_length(key):
    if isinstance(key, (str, bytes)):
        return _base64_decode_length(key) is 16
    raise KeyError('the key must be str or bytes')

# check base64.b64decode string length
def _base64_decode_length(key):
    if isinstance(key, (str, bytes)):
        return len(base64.b64decode(key))
    raise KeyError('the key must be str or bytes')

def http_header_parser(raw_header):
    header = to_string(raw_header)
    lines = list(filter(lambda l: l != '', header.split('\r\n')))
    request_line = Request_Line(*map(lambda s: s.strip(), lines.pop(0).split(' ')))
    header_fields = list(map(lambda l: Header_Field(*map(lambda s: s.strip(), l.split(':', 1))), lines))

    return Request_Header(request_line, header_fields)

def http_header_generate(status_code, header_fields, http_version = HTTP_VERSION_1_1, status_description = None):
    pass
