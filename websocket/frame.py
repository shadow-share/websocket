#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#

'''
A high-level overview of the framing is given in the following figure.
B 0 * * * * * * * 1 * * * * * * * 2 * * * * * * * 3 * * * * * * * -
  |               |               |               |               |
b 0               |   1           |       2       |           3   |
  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 |
 +-+-+-+-+-------+-+-------------+-------------------------------+
 |F|R|R|R| opcode|M| Payload len |    Extended payload length    |
 |I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
 |N|V|V|V|       |S|             |   (if payload len==126/127)   |
 | |1|2|3|       |K|             |                               |
 +-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
 |     Extended payload length continued, if payload len == 127  |
 + - - - - - - - - - - - - - - - +-------------------------------+
 |                               |Masking-key, if MASK set to 1  |
 +-------------------------------+-------------------------------+
 | Masking-key (continued)       |          Payload Data         |
 +-------------------------------- - - - - - - - - - - - - - - - +
 :                     Payload Data continued ...                :
 + - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - +
 |                     Payload Data continued ...                |
 +---------------------------------------------------------------+

FIN:  1 bit

      Indicates that this is the final fragment in a message.  The first
      fragment MAY also be the final fragment.


RSV1, RSV2, RSV3:  1 bit each

      MUST be 0 unless an extension is negotiated that defines meanings
      for non-zero values.  If a nonzero value is received and none of
      the negotiated extensions defines the meaning of such a nonzero
      value, the receiving endpoint MUST _Fail the WebSocket
      Connection_.


Opcode:  4 bits

      Defines the interpretation of the "Payload data".  If an unknown
      opcode is received, the receiving endpoint MUST _Fail the
      WebSocket Connection_.  The following values are defined.

      *  %x0 denotes a continuation frame

      *  %x1 denotes a text frame

      *  %x2 denotes a binary frame

      *  %x3-7 are reserved for further non-control frames

      *  %x8 denotes a connection close

      *  %x9 denotes a ping

      *  %xA denotes a pong

      *  %xB-F are reserved for further control frames


Mask:  1 bit

      Defines whether the "Payload data" is masked.  If set to 1, a
      masking key is present in masking-key, and this is used to unmask
      the "Payload data" as per Section 5.3.  All frames sent from
      client to server have this bit set to 1.


Payload length:  7 bits, 7+16 bits, or 7+64 bits

      The length of the "Payload data", in bytes: if 0-125, that is the
      payload length.  If 126, the following 2 bytes interpreted as a
      16-bit unsigned integer are the payload length.  If 127, the
      following 8 bytes interpreted as a 64-bit unsigned integer (the
      most significant bit MUST be 0) are the payload length.  Multibyte
      length quantities are expressed in network byte order.  Note that
      in all cases, the minimal number of bytes MUST be used to encode
      the length, for example, the length of a 124-byte-long string
      can't be encoded as the sequence 126, 0, 124.  The payload length
      is the length of the "Extension data" + the length of the
      "Application data".  The length of the "Extension data" may be
      zero, in which case the payload length is the length of the
      "Application data".


Masking-key:  0 or 4 bytes

      All frames sent from the client to the server are masked by a
      32-bit value that is contained within the frame.  This field is
      present if the mask bit is set to 1 and is absent if the mask bit
      is set to 0.  See Section 5.3 for further information on client-
      to-server masking.


Payload data:  (x+y) bytes

      The "Payload data" is defined as "Extension data" concatenated
      with "Application data".


Extension data:  x bytes

      The "Extension data" is 0 bytes unless an extension has been
      negotiated.  Any extension MUST specify the length of the
      "Extension data", or how that length may be calculated, and how
      the extension use MUST be negotiated during the opening handshake.
      If present, the "Extension data" is included in the total payload
      length.


Application data:  y bytes

      Arbitrary "Application data", taking up the remainder of the frame
      after any "Extension data".  The length of the "Application data"
      is equal to the payload length minus the length of the "Extension
      data".

'''
import abc
import socket
import struct
from websocket import utils

# 0x1 = 0 0 0 0 0 0 0 1 => [ 1, 0, 0, 0, 0, 0, 0, 0 ]
# 0x2 = 0 0 0 0 0 0 1 0 => [ 0, 1, 0, 0, 0, 0, 0, 0 ]
def number_to_bit_array(number):
    if not isinstance(number, int):
        raise TypeError('the number must be int type')

    bit_length = len(bin(number)[2:])
    bit_array = [0] * (((bit_length // 8) + (0 if (bit_length % 8 == 0) else 1)) * 8)

    for _bit_index in range(bit_length):
        bit_array[_bit_index] = number & 0x1
        number = number >> 1

    return bit_array

def string_to_bit_array(string):
    return number_to_bit_array(int(utils.to_bytes(string).hex(), 16))[::-1]

def bit_array_to_octet_array(bit_array):
    if not isinstance(bit_array, list):
        raise KeyError('bit array must be list type')
    else:
        if len(bit_array) % 8 != 0:
            raise RuntimeError('bit array is invalid list')

    return [ tuple(bit_array[oi * 8:(oi + 1) * 8]) for oi in range(len(bit_array) // 8) ]

def string_to_octet_array(string):
    return bit_array_to_octet_array(string_to_bit_array(string))

def bin_to_number(bin_string):
    return int(bin_string, 2)

def number_to_byte_string(number):
    if not isinstance(number, int):
        raise KeyError('the number is not int type')

    byte_string_rst = b''
    while number:
        byte_string_rst += struct.pack('!B', number & 0xff)
        number >>= 8
    return byte_string_rst

def bit_array_to_bin_string(bit_array):
    if not isinstance(bit_array, (list, tuple)):
        raise KeyError('bit array is not list type')

    bit_string = ''
    for bit in bit_array:
        bit_string += str(bit)
    return utils.to_bytes(bit_string)

def octet_to_number(octet):
    return int(''.join([ str(bit) for bit in octet ]), 2)

def ws_generate_frame_mask_key():
    # 2 ^ 4 = 16 -> 0x10
    # 0xF = 15 -> 4-bit
    # 0x00 - 0xFF = 1byte(8 bit)
    # 4 * 8 = 32 bit
    return utils.random_bytes_string(4, start = 0x00, stop = 0xff)

def ws_transform_payload_data(data, mask_key):
    if not isinstance(mask_key, (int)):
        if isinstance(mask_key, str):
            mask_key = int(mask_key, 16)
        else:
            raise KeyError('mask key must be hex int')
    if not isinstance(data, (str, bytes)):
        raise KeyError('data must be str or bytes type')

    mask_key_octet = {
        0: (mask_key & 0xff000000) >> 24,
        1: (mask_key & 0x00ff0000) >> 16,
        2: (mask_key & 0x0000ff00) >> 8,
        3: mask_key & 0x000000ff
    }

    transformed_string = b''
    for index, value in enumerate(data):
        transformed_string += struct.pack('!B', (value ^ mask_key_octet[index % 4]) & 0xff)
    return transformed_string

class Frame_Base(object, metaclass = abc.ABCMeta):

    def __init__(self):
        pass

    @property
    def flag_fin(self):
        return True

    @property
    def flag_rsv1(self):
        return 0

    @property
    def flag_rsv2(self):
        return 0

    @property
    def flag_rsv3(self):
        return 0

    @property
    def flag_opcode(self):
        return 0

    @property
    def flag_mask(self):
        return True
    
    @property
    def payload_data_length(self):
        return 0

    @property
    def extension_data_length(self):
        return 0

    @property
    def application_data_length(self):
        return 0

    @property
    def mask_key(self):
        return b''

    @property
    def payload_data(self):
        return b''
    
    @property
    def extension_data(self):
        return b''

    @property
    def application_data(self):
        return b''

class Client_To_Server_Frame(Frame_Base):
    pass

class Server_To_Client_Frame(Frame_Base):
    pass

class Frame_Parser(object):

    def __init__(self):
        pass

def create_c2s_frame():
    pass

def create_s2c_frame():
    pass

def frame_parser():
    pass

PAYLOAD_LENGTH_16 = -1
PAYLOAD_LENGTH_64 = -2

# the most significant bit MUST be 0
def parse_frame_length(frame_header):
    if not isinstance(frame_header, (str, bytes)):
        raise KeyError('frame_header must be str or bytes type')
    octet_array = string_to_octet_array(frame_header)
    if len(octet_array) < 2:
        raise KeyError('frame_header invalid')

    # first bit is MASK flag
    payload_length = octet_to_number(octet_array[1][1:])
    if payload_length <= 125:
        return payload_length
    elif payload_length == 126:
        if len(octet_array) < 4:
            return PAYLOAD_LENGTH_16
        else:
            return octet_to_number(utils.flatten_list(octet_array[2:5]))
    elif payload_length == 127:
        if len(octet_array) < 4:
            return PAYLOAD_LENGTH_64
        else:
            return octet_to_number(utils.flatten_list(octet_array[2:11]))

def receive_single_frame(socket_fd):
    if not isinstance(socket_fd, socket.socket):
        raise KeyError('socket_fd must be socket.socket instance')
    frame_contents = socket_fd.recv(2)
    frame_length = parse_frame_length(frame_contents)

    print('parse_frame_length return value', frame_length)

    if frame_length is PAYLOAD_LENGTH_16:
        frame_contents += socket_fd.recv(2)
    elif frame_length is PAYLOAD_LENGTH_64:
        frame_contents += socket_fd.recv(8)
    frame_length = parse_frame_length(frame_contents)
    if frame_length < 0:
        raise RuntimeError('receive_single_frame method internal error')

    print('parse_frame_length again return value', frame_length)

    # Client-To-Server have Mask-Key(4Bytes)
    octet_array = string_to_octet_array(frame_contents)
    if (octet_array[1][0] == 1):
        frame_length += 4

    print('Client-To-Server check', frame_length)

    frame_contents += socket_fd.recv(frame_length)
    return frame_contents

