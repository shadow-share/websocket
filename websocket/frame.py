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


def ws_transform_payload_data(data, mask_key):
    if not isinstance(mask_key, (int)):
        if isinstance(mask_key, str):
            mask_key = int(mask_key, 16)
        else:
            raise KeyError('mask key must be hex int')
    if not isinstance(data, (str, bytes)):
        raise KeyError('data must be str or bytes type')

    # Octet i of the transformed data is the XOR of octet i
    # of the original data with octet at index i modulo 4
    # of the masking key
    mask_key_octet = {
        0: (mask_key & 0xff000000) >> 24,
        1: (mask_key & 0x00ff0000) >> 16,
        2: (mask_key & 0x0000ff00) >> 8,
        3: mask_key & 0x000000ff
    }

    transformed_string = b''
    for index, value in enumerate(utils.to_bytes(data)):
        transformed_string += struct.pack('!B', (value ^ mask_key_octet[index % 4]) & 0xff)
    return transformed_string

PAYLOAD_LENGTH_16 = -1
PAYLOAD_LENGTH_64 = -2

# the most significant bit MUST be 0
def parse_frame_length(frame_header):
    if not isinstance(frame_header, (str, bytes)):
        raise KeyError('frame_header must be str or bytes type')
    octet_array = utils.string_to_octet_array(frame_header)
    if len(octet_array) < 2:
        raise KeyError('frame_header invalid')

    # first bit is MASK flag
    payload_length = utils.octet_to_number(octet_array[1][1:])
    # if 0-125, that is the payload length
    if payload_length <= 125:
        return payload_length
    # If 126, the following 2 bytes interpreted as a
    # 16-bit unsigned integer are the payload length
    elif payload_length == 126:
        if len(octet_array) < 4:
            return PAYLOAD_LENGTH_16
        else:
            return utils.octet_to_number(utils.flatten_list(octet_array[2:4]))
    # If 127, the following 8 bytes interpreted as a
    # 64-bit unsigned integer (the most significant bit
    # MUST be 0) are the payload length.
    elif payload_length == 127:
        if len(octet_array) < 10:
            return PAYLOAD_LENGTH_64
        else:
            return utils.octet_to_number(utils.flatten_list(octet_array[2:10]))
    else:
        raise RuntimeError('fatal error, 0 <= 7-bits number <= 127')

def receive_single_frame(socket_fd):
    if not isinstance(socket_fd, socket.socket):
        raise KeyError('socket_fd must be socket.socket instance')
    frame_contents = socket_fd.recv(2)
    frame_length = parse_frame_length(frame_contents)

    if frame_length is PAYLOAD_LENGTH_16:
        frame_contents += socket_fd.recv(2)
    elif frame_length is PAYLOAD_LENGTH_64:
        frame_contents += socket_fd.recv(8)
    frame_length = parse_frame_length(frame_contents)
    if frame_length < 0:
        raise RuntimeError('receive_single_frame method internal error')

    # Client-To-Server have Mask-Key(4Bytes)
    octet_array = utils.string_to_octet_array(frame_contents)
    if (octet_array[1][0] == 1):
        frame_length += 4

    frame_contents += socket_fd.recv(frame_length)
    return frame_contents

class Frame_Base(object, metaclass = abc.ABCMeta):

    def __init__(self, raw_frame_bit_array):
        if len(raw_frame_bit_array) % 8 != 0:
            raise RuntimeError('the raw frame bit array is invalid')
        self._octet_array = utils.bit_array_to_octet_array(raw_frame_bit_array)
        self.parse_octet()

        self._global_frame_type = {
            0x0: b'Continuation Frame',
            0x1: b'Text Frame',
            0x2: b'Binary Frame',
            0x3: b'Non-Control Frame',
            0x4: b'Non-Control Frame',
            0x5: b'Non-Control Frame',
            0x6: b'Non-Control Frame',
            0x7: b'Non-Control Frame',
            0x8: b'Close Frame',
            0x9: b'Ping Frame',
            0xA: b'Pong Frame',
            0xB: b'Control Frame',
            0xC: b'Control Frame',
            0xD: b'Control Frame',
            0xE: b'Control Frame',
            0xF: b'Control Frame',
        }

    def parse_octet(self):
        # first byte(8-bits)
        # +-+-+-+-+-------+
        # |F|R|R|R| opcode|
        # |I|S|S|S|  (4)  |
        # |N|V|V|V|       |
        # | |1|2|3|       |
        # +-+-+-+-+-------+
        self._fin_flag = self._octet_array[0][0]
        self._rsv1_flag = self._octet_array[0][1]
        self._rsv2_flag = self._octet_array[0][2]
        self._rsv3_flag = self._octet_array[0][3]
        self._opcode_flag = utils.octet_to_number(self._octet_array[0][4:])
        # second byte(8-bits)
        # +-+-------------+
        # |M| Payload len |
        # |A|     (7)     |
        # |S|             |
        # |K|             |
        # +-+-+-+-+-------+
        self._mask_flag = self._octet_array[1][0]
        self._payload_length = utils.octet_to_number(self._octet_array[1][1:])

        _last_byte_index = 2
        if self._payload_length is 126:
            # If 126, the following 2 bytes interpreted as a
            # 16-bit unsigned integer are the payload length
            self._payload_length = utils.octet_to_number(utils.flatten_list(self._octet_array[2:4]))
            _last_byte_index = 4
        elif self._payload_length is 127:
            # If 127, the following 8 bytes interpreted as a
            # 64-bit unsigned integer (the most significant bit
            # MUST be 0) are the payload length.
            self._payload_length = utils.octet_to_number(utils.flatten_list(self._octet_array[2:10]))
            _last_byte_index = 10

        # Masking-key, if MASK set to 1
        if self._mask_flag is 1:
            self._mask_key = utils.octet_to_number(
                utils.flatten_list(self._octet_array[_last_byte_index:_last_byte_index + 4])
            )
            _last_byte_index += 4
        else:
            self._mask_key = False

        # Payload Data
        self._payload_data = utils.octet_array_to_string(self._octet_array[_last_byte_index:])
        if self._mask_flag is 1:
            self._payload_data = ws_transform_payload_data(self._payload_data, self._mask_key)

    @property
    def flag_fin(self):
        return self._fin_flag

    @property
    def flag_rsv1(self):
        return self._rsv1_flag

    @property
    def flag_rsv2(self):
        return self._rsv2_flag

    @property
    def flag_rsv3(self):
        return self._rsv3_flag

    @property
    def flag_opcode(self):
        return self._opcode_flag

    @property
    def flag_mask(self):
        return self._mask_flag
    
    @property
    def payload_data_length(self):
        return self._payload_length

    @property
    def mask_key(self):
        return self._mask_key

    @property
    def payload_data(self):
        return self._payload_data
    @property
    def frame_type(self):
        return self._global_frame_type[self._opcode_flag]


class Frame_Parser(Frame_Base):

    def __init__(self, socket_fd):
        bit_array = utils.string_to_bit_array(receive_single_frame(socket_fd))
        super(Frame_Parser, self).__init__(bit_array)


class Frame_Generator(object):

    def __init__(self):
        self._flag_fin = 1
        self._flag_rsv1 = 0
        self._flag_rsv2 = 0
        self._flag_rsv3 = 0

        self._flag_mask = 0
        self._mask_key = False

    def enable_fin(self):
        self._flag_fin = 1
        return self

    def disable_fin(self):
        self._flag_fin = 0
        return self

    def enable_rsv1(self):
        self._flag_rsv1 = 1
        return self

    def disable_rsv1(self):
        self._flag_rsv1 = 0
        return self

    def enable_rsv2(self):
        self._flag_rsv2 = 1
        return self

    def disable_rsv2(self):
        self._flag_rsv2 = 0
        return self

    def enable_rsv3(self):
        self._flag_rsv3 = 1
        return self

    def disable_rsv3(self):
        self._flag_rsv3 = 0
        return self

    def set_mask_key(self, mask_key):
        self._flag_mask = 1
        self._mask_key = mask_key
        return self

