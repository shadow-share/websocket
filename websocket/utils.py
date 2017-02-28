#!/usr/bin/env python3
#
# Copyright (C) 2017 ShadowMan
#
import math
import base64
import random
import socket
import struct
import hashlib
from collections import namedtuple

# Response status code description
_response_status_code_description = {
    101: b'Switching Protocols',
    400: b'Bad Request',
    401: b'',
    403: b'Forbidden',
    404: b'Not Found',
    426: b'Upgrade Required'
}

# Request line namedtuple
Request_Line = namedtuple('Request_Line', 'method path version')

# Header item namedtuple
Header_Field = namedtuple('Header_Item', 'key value')

# Request header namedtuple
Request_Header = namedtuple('Request_Header', 'lead fields')

# GUID String
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
def random_bytes_string(string_length, start = 0, stop = 0x7f, encoding = 'utf-8'):
    rst_string = b''
    for _ in range(string_length):
        rst_string += chr(random.randint(start, stop)).encode(encoding)
    return rst_string

# The value of this header field MUST be a
# nonce consisting of a randomly selected 16-byte value that has
# been base64-encoded (see Section 4 of [RFC4648]).  The nonce
# MUST be selected randomly for each connection.
def ws_generate_key():
    random_16byte_string = random_bytes_string(16)
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

def http_header_generate(status_code, header_fields, status_description = None):
    response = b''
    if status_code in _response_status_code_description:
        status_description = \
            _response_status_code_description[status_code] if status_description == None else status_description
    response += b'HTTP/1.1' + b' ' + to_bytes(str(status_code)) + b' ' + status_description + b'\r\n'

    for field in header_fields:
        response += field.key + b': ' + field.value + b'\r\n'
    response += b'\r\n'
    return response

def flatten_list(array):
    for item in array:
        if isinstance(item, (tuple, list)):
            yield from flatten_list(item)
        else:
            yield item

# 0x1 = 0 0 0 0 0 0 0 1 => [ 1, 0, 0, 0, 0, 0, 0, 0 ]
# 0x2 = 0 0 0 0 0 0 1 0 => [ 0, 1, 0, 0, 0, 0, 0, 0 ]
def number_to_bit_array(number, pad_byte = 1):
    if not isinstance(number, int):
        raise TypeError('the number must be int type')

    bit_length = len(bin(number)[2:])
    # if number is 0, fill to 1-byte
    if bit_length is 0:
        bit_length = pad_byte * 8
    bit_array = [0] * (((bit_length // 8) + (0 if (bit_length % 8 == 0) else 1)) * 8)

    for _bit_index in range(bit_length):
        bit_array[_bit_index] = number & 0x1
        number = number >> 1
    return bit_array

def string_to_bit_array(string):
    bit_array = []
    for char in string:
        bit_array += number_to_bit_array(char)[::-1]
    return bit_array
    # return number_to_bit_array(int(to_bytes(string).hex(), 16))[::-1]

def bit_array_to_octet_array(bit_array):
    if not isinstance(bit_array, list):
        raise KeyError('bit array must be list type')
    else:
        if len(bit_array) % 8 != 0:
            raise RuntimeError('bit array is invalid list')

    return [ tuple(bit_array[oi * 8:(oi + 1) * 8]) for oi in range(len(bit_array) // 8) ]

def string_to_octet_array(string):
    return bit_array_to_octet_array(string_to_bit_array(string))

def binary_string_to_number(binary_string):
    return int(binary_string, 2)

def number_to_byte_string(number):
    if not isinstance(number, int):
        raise KeyError('the number is not int type')

    byte_string_rst = b''
    if number is 0:
        byte_string_rst = b'\x00'
    else:
        while number:
            byte_string_rst += struct.pack('!B', number & 0xff)
            number >>= 8
    return byte_string_rst

def bit_array_to_binary_string(bit_array):
    if not isinstance(bit_array, (list, tuple)):
        raise KeyError('bit array is not list type')

    bit_string = ''
    for bit in bit_array:
        bit_string += str(bit)
    return to_bytes(bit_string)

def octet_to_number(octet):
    return int(''.join([ str(b) for b in octet ]), 2)

def bit_array_to_string(bit_array):
    if not isinstance(bit_array, (list, tuple)):
        raise KeyError('bit array is not list type')

    string_rst = b''
    binary_string = bit_array_to_binary_string(bit_array)
    # get 32-bits data
    for index in range(0, math.floor(len(binary_string) / 32) * 32, 32):
        string_rst += number_to_byte_string(
            # network byte-order -> native byte-order
            socket.ntohl(binary_string_to_number(binary_string[index:index + 32]))
        )
    if len(binary_string) % 32 != 0:
        for index in range(math.floor(len(binary_string) / 32) * 32, len(binary_string), 8):
            string_rst += number_to_byte_string(
                binary_string_to_number(binary_string[index:index + 8])
            )
    return string_rst

def octet_array_to_string(octet_array):
    string_rst = b''
    for octet in octet_array:
        string_rst += number_to_byte_string(octet_to_number(octet))
    return string_rst
