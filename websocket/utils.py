#!/usr/bin/env python3
#
# Copyright (C) 2017 ShadowMan
#
import math
import array
import base64
import random
import socket
import struct


def to_string(byte_string, encoding = 'utf-8'):
    if not isinstance(byte_string, str):
        if hasattr(byte_string, 'decode'):
            return byte_string.decode(encoding)
        else:
            raise TypeError('the byte_string has\'t decode method')
    elif isinstance(byte_string, str):
        return byte_string
    else:
        raise TypeError('the byte_string is invalid')


def to_bytes(string, encoding = 'utf-8'):
    if not isinstance(string, bytes):
        if hasattr(string, 'encode'):
            return string.encode(encoding)
        else:
            raise KeyError('the string has\'t encode method')
    elif isinstance(string, bytes):
        return string
    else:
        raise TypeError('the string is invalid')


# a nonce consisting of a randomly selected 16-byte value
# 1-byte(0 - 127), not 0 - 255
def random_bytes_string(string_length, start = 0, stop = 0x7f, encoding = 'utf-8'):
    rst_string = ''
    for _ in range(string_length):
        rst_string += chr(random.randint(start, stop))
    return rst_string.encode(encoding)


# check base64.b64decode string length
def base64_decode_length(key):
    if isinstance(key, (str, bytes)):
        return len(base64.b64decode(key))
    raise KeyError('the key must be str or bytes')


# [ 1, 2, (3, 4), [ 5, (6, 7), 8 ], 9 ] =>
# [ 1, 2, 3, 4, 5, 6, 7, 8, 9 ]
def flatten_list(array):
    def _flatten_generator(array):
        for item in array:
            if isinstance(item, (tuple, list)):
                yield from flatten_list(item)
            else:
                yield item
    return list(_flatten_generator(array))


# 0x1 = 0 0 0 0 0 0 0 1 => [ 1, 0, 0, 0, 0, 0, 0, 0 ]
# 0x2 = 0 0 0 0 0 0 1 0 => [ 0, 1, 0, 0, 0, 0, 0, 0 ]
# TODO  list -> array
def number_to_bit_array(number, pad_byte = 1):
    if not isinstance(number, int):
        raise TypeError('the number must be int type')

    bit_length = len(bin(number)[2:])
    # if number is 0, fill to 1-byte
    if bit_length is 0:
        bit_length = pad_byte * 8
    bit_array = [0] * (((bit_length // 8) + (0 if (bit_length % 8 == 0) else 1)) * 8)
    if (len(bit_array) < pad_byte * 8):
        bit_array = [ 0 ] * pad_byte * 8

    for _bit_index in range(bit_length):
        bit_array[_bit_index] = number & 0x1
        number = number >> 1

    return bit_array


def string_to_bit_array(string):
    bit_array = []
    for char in to_bytes(string):
        bit_array += number_to_bit_array(char)
    return bit_array
    # return number_to_bit_array(int(to_bytes(string).hex(), 16))[::-1]


def octet_array_to_big_endian(octet_array):
    if struct.pack('h', 0x0102)[0] is 0x01:
        return octet_array
    return octet_array[::-1]


def bit_array_to_octet_array(bit_array, big_endian = False):
    if not isinstance(bit_array, list):
        raise KeyError('bit array must be list type')
    else:
        if len(bit_array) % 8 != 0:
            raise RuntimeError('bit array is invalid list')
    if big_endian is True:
        if struct.pack('h', 0x0102)[0] is 0x02:
            return [ tuple(bit_array[oi * 8:(oi + 1) * 8])[::-1] for oi in range(len(bit_array) // 8) ][::-1]
    return [ tuple(bit_array[oi * 8:(oi + 1) * 8])[::-1] for oi in range(len(bit_array) // 8) ]


def string_to_octet_array(string):
    return bit_array_to_octet_array(string_to_bit_array(string))


def binary_string_to_number(binary_string):
    return int(binary_string, 2)


def number_to_byte_string(number, pad_byte_count = 1):
    if not isinstance(number, int):
        raise KeyError('the number is not int type')

    byte_string_rst = b''
    if number is 0:
        byte_string_rst = b'\x00' * pad_byte_count
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


def empty_method():
    pass

