#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#
import ctypes
import struct
from websocket.utils import generic, exceptions

'''c
typedef union {
    struct {
        unsigned b0 : 1;
        unsigned b1 : 1;
        unsigned b2 : 1;
        unsigned b3 : 1;
        unsigned b4 : 1;
        unsigned b5 : 1;
        unsigned b6 : 1;
        unsigned b7 : 1;
    } _Bits;
    unsigned char value;
} Byte;
'''
class Byte(ctypes.Union):

    class _Bits(ctypes.Structure):

        _fields_ = [
            ('b7', ctypes.c_uint8, 1), ('b6', ctypes.c_uint8, 1),
            ('b5', ctypes.c_uint8, 1), ('b4', ctypes.c_uint8, 1),
            ('b3', ctypes.c_uint8, 1), ('b2', ctypes.c_uint8, 1),
            ('b1', ctypes.c_uint8, 1), ('b0', ctypes.c_uint8, 1),
        ]

    _fields_ = [
        ('value', ctypes.c_char),
        ('bits', _Bits)
    ]
    _anonymous_ = ('bits',)

    def __init__(self, octet_data):
        super(Byte, self).__init__()
        if isinstance(octet_data, int):
            self.value = octet_data & 0xff
        else:
            raise exceptions.ParameterError('octet data must be 1-byte length')


class ByteArray(object):
    '''
    :type raw_data: int | bytes | str | None
    :type size: int
    :type elements: deque
    '''
    def __init__(self, raw_data):
        if raw_data is None:
            self.size = 0
            # deque is not support slice
            self.elements = list()  # type: list
        elif isinstance(raw_data, int):
            self._factory_from_int(raw_data)
        elif isinstance(raw_data, bytes):
            self._factory_from_bytes(raw_data)
        elif isinstance(raw_data, str):
            self._factory_from_bytes(generic.to_bytes(raw_data))
        else:
            raise exceptions.ParameterError('raw data type invalid')

    def _factory_from_int(self, raw_data):
        hex_string = hex(raw_data)[2:]  # strip 0x
        if len(hex_string) % 2:
            hex_string = '0' + hex_string
        self.size = int(len(hex_string) / 2)
        self.elements = list(list(
            map(lambda el: Byte(el), [
                int(hex_string[index:index + 2], 16)
                    for index in range(0, len(hex_string), 2)
                ]
            )
        ))

    def _factory_from_bytes(self, raw_data):
        self.size = len(raw_data)
        self.elements = list(
            map(lambda el: Byte(el), [
                el for el in raw_data
            ])
        )

    def build(self, start = 0):
        self._check_index(start)
        return struct.pack('!{}B'.format(self.size - start), *[
            ord(byte.value) for byte in self.elements[start:]
        ])

    def to_integer(self):
        return generic.to_integer(self.build())

    def get_bits(self, index, length = 1):
        self._check_index(index)
        self._check_index(index + length)
        bytes = self.elements[index:index + length]
        if len(bytes) == 1:
            byte = bytes[0]
            return (byte.b0, byte.b1, byte.b2, byte.b3,
                    byte.b4, byte.b5, byte.b6, byte.b7)
        else:
            return [
                (byte.b0, byte.b1, byte.b2, byte.b3,
                 byte.b4, byte.b5, byte.b6, byte.b7) for byte in bytes
            ]

    def get_bit(self, index, offset):
        self._check_index(index)
        if 7 < offset < 0:
            raise exceptions.ParameterError('bit offset invalid')
        return self.get_bits(index)[offset]

    def _check_index(self, index):
        if index > self.size or index < 0:
            raise exceptions.ParameterError('operator index invalid')
        return True

    def __len__(self):
        return self.size

    def __str__(self):
        return '<{} size={}>'.format(self.__class__.__name__, self.size)


class Packet(ByteArray):

    def __init__(self, value = None):
        super(Packet, self).__init__(value)


    def update(self, raw_data):
        ba = ByteArray(raw_data)
        self.size += ba.size
        self.elements += ba.elements

    def modify(self, index, value):
        self._check_index(index)
        self.elements[index].value = generic.to_int8(value)

    def insert(self, index, value):
        self._check_index(index)
        self.elements.insert(index, Byte(generic.to_int8(value)))
        self.size += 1

    def put_int8(self, value):
        self.insert(self.size, value)

    def put_int16(self, value):
        self.insert(self.size, (value & 0xff00) >> 8)
        self.insert(self.size, (value & 0x00ff) >> 0)

    def put_int32(self, value):
        self.put_int16((value & 0xffff0000) >> 16)
        self.put_int16((value & 0x0000ffff) >> 0)

    def put_int64(self, value):
        self.put_int32((value & 0xffffffff00000000) >> 32)
        self.put_int32((value & 0x00000000ffffffff) >> 0)


    def put_bits(self, *bits):
        bit_length = len(bits)
        if bit_length < 8:
            octet = ([ 0 ] * (8 - bit_length)) + list(bits)
        else:
            octet = bits[0:8]
        self.put_int8(int(''.join([ str(b) for b in octet ]), 2))

    def put_string(self, value):
        self.update(value)

    def get_int8(self, index = None):
        if index is None:
            index = self.size - 1
        self._check_index(index)
        return self.elements[index].value

    def get_int16(self, index = None):
        if index is None:
            index = self.size - 2
        self._check_index(index)
        self._check_index(index + 2)
        return b''.join([el.value for el in self.elements[index:(index + 2)]])

    def get_int32(self, index = None):
        if index is None:
            index = self.size - 4
        self._check_index(index)
        self._check_index(index + 4)
        return b''.join([el.value for el in self.elements[index:(index + 4)]])

    def get_int64(self, index = None):
        if index is None:
            index = self.size - 8
        self._check_index(index)
        self._check_index(index + 8)
        return b''.join([el.value for el in self.elements[index:(index + 8)]])


    def get_last(self, length):
        self._check_index(length)
        return b''.join([el.value for el in self.elements[-1:-length - 1:-1][::-1]])

    def clear(self):
        self.elements.clear()
        self.size = 0


def bits_to_integer(bits_array):
    return int(''.join([ str(b) for b in bits_array ]), 2)


def number_to_bits(number, pad_bit_length = 0):
    if not isinstance(number, int):
        raise exceptions.ParameterError('number must be integer')
    bits = [ int(i) for i in bin(number)[2:] ]
    if len(bits) < pad_bit_length:
        return ([ 0 ] * (pad_bit_length - len(bits))) + bits
    return bits

if __name__ == '__main__':
    def test_packet():
        packet = Packet()

        packet.put_int8(0xaa)
        assert packet.get_int8(0) == b'\xaa'

        packet.put_int8('CA')
        assert packet.get_int16(0) == b'\xaaA'

        packet.put_int16(0x12345678)
        assert packet.get_int16(2) == b'\x56\x78'

        packet.put_int32(0xabcdef11)
        assert packet.get_int8() == b'\x11'
        assert packet.get_int16() == b'\xef\x11'
        assert packet.get_int32() == b'\xab\xcd\xef\x11'

        packet.put_int32(0x0)
        assert packet.get_int8() == b'\x00'
        assert packet.get_int16() == b'\x00\x00'
        assert packet.get_int32() == b'\x00\x00\x00\x00'

        packet.put_bits(0, 0, 0, 0, 0, 0, 1, 0)
        assert packet.get_int8() == b'\x02'

        packet.put_int64(0x12345678abcdef00)
        assert packet.get_int32() == b'\xab\xcd\xef\x00'
        assert packet.get_int32(packet.size - 8) == b'\x12\x34\x56\x78'


        packet.put_string(b'Hello World')
        assert packet.get_last(len(b'Hello World')) == b'Hello World'

        packet.clear()
        assert packet.size == 0
    test_packet()