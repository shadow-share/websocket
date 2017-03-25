#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#
import base64
import random


def to_string(object, encoding = 'utf-8'):
    if isinstance(object, str):
        return object
    if isinstance(object, bytes):
        return object.decode(encoding)
    if hasattr(object, '__str__'):
        return object.__str__()
    raise TypeError('object to string error occurs, object invalid')


def to_bytes(object, encoding = 'utf-8'):
    if isinstance(object, bytes):
        return object
    if isinstance(object, str):
        return object.encode(encoding)
    if hasattr(object, '__str__'):
        return object.__str__().encode(encoding)
    raise TypeError('object to bytes error occurs, object invalid')


def to_integer(object, *, encoding = 'utf-8'):
    if isinstance(object, int):
        return object
    if isinstance(object, str):
        object = object.encode(encoding)
    if isinstance(object, bytes):
        return int(''.join([ hex(ch)[2:] for ch in object ]), 16)


def to_int8(object):
    return to_integer(object) & 0xff


def to_int16(object):
    return to_integer(object) & 0xffff


def to_int32(object):
    return to_integer(object) & 0xffffffff


# a nonce consisting of a randomly selected 16-byte value
# 1-byte(0 - 127), not 0 - 255
def random_bytes_string(length, start = 0, stop = 0x7f, encoding = 'utf-8'):
    rst_string = \
        ''.join([ chr(random.randint(start, stop)) for _ in range(length) ])
    return to_bytes(rst_string, encoding)


# check base64.b64decode string length
def base64_decode_length(key):
    return len(base64.b64decode(to_bytes(key)))


# [ 1, 2, (3, 4), [ 5, (6, 7), 8 ], 9 ] =>
# [ 1, 2, 3, 4, 5, 6, 7, 8, 9 ]
def flatten_list(array):
    def _flatten_generator(array):
        for item in array:
            if isinstance(item, (tuple, list)):
                yield from _flatten_generator(item)
            else:
                yield item
    return list(_flatten_generator(array))

