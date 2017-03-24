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
import os
import abc
import struct

from websocket.utils import (
    generic, ws_utils, exceptions, packet, logger
)

def ws_transform_payload_data(data, mask_key):
    if not isinstance(mask_key, (int)):
        # from string transition to int
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
    for index, value in enumerate(generic.to_bytes(data)):
        transformed_string += struct.pack('!B', (
        value ^ mask_key_octet[index % 4]) & 0xff)
    return transformed_string


def parse_frame_length(frame_header):
    if not isinstance(frame_header, (str, bytes)):
        raise KeyError('frame_header must be str or bytes type')
    header = packet.ByteArray(frame_header)
    if len(header) < 2:
        logger.warning('receive less than 2-bytes')
        raise RuntimeError('frame header less than 2-bytes')
    # first bit is MASK flag
    payload_length = packet.bits_to_integer(header.get_bits(1)[1:])
    # if 0-125, that is the payload length
    if payload_length <= 125:
        # if frame is client-to-server, payload length does not include mask-key(4-byte)
        if header.get_bits(1)[0] is 1:
            return payload_length + 6
        return payload_length + 2
    # If 126, the following 2 bytes interpreted as a
    # 16-bit unsigned integer are the payload length
    elif payload_length == 126:
        # Payload length field is in [2-4)bytes
        if len(header) < 4:
            raise exceptions.FrameHeaderParseError(
                'payload length flag is 126, but header length is {}'.format(
                    len(header)))
        if header.get_bits(1)[0] is 1:
            return packet.bits_to_integer(
                generic.flatten_list(header.get_bits(2, 2))) + 8
        return packet.bits_to_integer(
            generic.flatten_list(header.get_bits(2, 2))) + 4
    # If 127, the following 8 bytes interpreted as a
    # 64-bit unsigned integer (the most significant bit
    # MUST be 0) are the payload length.
    elif payload_length == 127:
        # Payload length field is in [2-10)bytes
        if len(header) < 10:
            raise exceptions.FrameHeaderParseError(
                'payload length flag is 127, but header length is {}'.format(
                    len(header)))
        if header.get_bits(1)[0] is 1:
            return packet.bits_to_integer(
                generic.flatten_list(header.get_bits(2, 2))) + 14
        return packet.bits_to_integer(
            generic.flatten_list(header.get_bits(2, 2))) + 10
    raise exceptions.FatalError('internal error')


# using for judge frame type
Text_Frame = b'Text Frame'
Binary_Frame = b'Binary Frame'
Close_Frame = b'Close Frame'


class FrameBase(object, metaclass=abc.ABCMeta):
    _global_frame_type = {
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

    def __init__(self, byte_array):
        if not isinstance(byte_array, packet.ByteArray):
            raise RuntimeError('the byte array is invalid')
        self._byte_array = byte_array
        # parse frame
        self.parse_octet()

    def parse_octet(self):
        # first byte(8-bits)
        # +-+-+-+-+-------+
        # |F|R|R|R| opcode|
        # |I|S|S|S|  (4)  |
        # |N|V|V|V|       |
        # | |1|2|3|       |
        # +-+-+-+-+-------+
        self._flag_fin = self._byte_array.get_bit(0, 0)
        self._flag_rsv1 = self._byte_array.get_bit(0, 1)
        self._flag_rsv2 = self._byte_array.get_bit(0, 2)
        self._flag_rsv3 = self._byte_array.get_bit(0, 3)
        self._flag_opcode = packet.bits_to_integer(
            self._byte_array.get_bits(0)[4:])
        # second byte(8-bits)
        # +-+-------------+
        # |M| Payload len |
        # |A|     (7)     |
        # |S|             |
        # |K|             |
        # +-+-+-+-+-------+
        self._flag_mask = self._byte_array.get_bit(1, 0)
        self._flag_payload_length = packet.bits_to_integer(
            self._byte_array.get_bits(1)[1:])
        self._payload_length = self._flag_payload_length

        _last_byte_index = 2
        if self._payload_length is 126:
            # If 126, the following 2 bytes interpreted as a
            # 16-bit unsigned integer are the payload length
            self._payload_length = packet.bits_to_integer(
                generic.flatten_list(
                    self._byte_array.get_bits(_last_byte_index, 2)))
            _last_byte_index = 4
        elif self._payload_length is 127:
            # If 127, the following 8 bytes interpreted as a
            # 64-bit unsigned integer (the most significant bit
            # MUST be 0) are the payload length.
            self._payload_length = packet.bits_to_integer(
                generic.flatten_list(
                    self._byte_array.get_bits(_last_byte_index, 8)))
            _last_byte_index = 10

        # Masking-key, if MASK set to 1
        if self._flag_mask is 1:
            self._mask_key = packet.bits_to_integer(
                generic.flatten_list(
                    self._byte_array.get_bits(_last_byte_index, 4)))
            _last_byte_index += 4
        else:
            self._mask_key = False

        # Payload Data
        self._payload_data = self._byte_array.build(_last_byte_index)
        if self._flag_mask is 1:
            self._payload_data = ws_transform_payload_data(self._payload_data,
                                                           self._mask_key)

    def pack(self):
        frame = packet.Packet()
        # first-byte
        frame.put_bits(
            self._flag_fin,  # FIN flag
            self._flag_rsv1,  # RSV1 flag
            self._flag_rsv2,  # RSV2 flag
            self._flag_rsv3,  # RSV3 flag
            *packet.number_to_bits(self._flag_opcode, 4)
        )
        # second-byte
        frame.put_bits(
            self._flag_mask,
            # Payload length flag [ <125, 126, 127 ]
            *packet.number_to_bits(self._flag_payload_length, 7)
        )
        # payload_length
        if self._flag_payload_length is 126:
            frame.put_int16(self.payload_data_length)
        elif self._flag_payload_length is 127:
            frame.put_int64(self.payload_data_length)
        # Masking key
        if self._flag_mask is 1:
            frame.put_int32(self._mask_key)
        # Payload data
        if self._flag_mask is 1:
            _payload_data = ws_transform_payload_data(self._payload_data,
                                                      self._mask_key)
            frame.put_string(_payload_data)
        else:
            frame.put_string(self._payload_data)
        return frame.build()

    @property
    def flag_fin(self):
        return self._flag_fin

    @property
    def flag_rsv1(self):
        return self._flag_rsv1

    @property
    def flag_rsv2(self):
        return self._flag_rsv2

    @property
    def flag_rsv3(self):
        return self._flag_rsv3

    @property
    def flag_opcode(self):
        return self._flag_opcode

    @property
    def flag_mask(self):
        return self._flag_mask

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
        return self._global_frame_type[self._flag_opcode]

    def __str__(self):
        return '<WebSocket-Frame Fin={fin_flag} Type=\'{type}\' Payload_length={payload_length} Mask_key={mask_key}>'.format(
            fin_flag = self.flag_fin,
            type = generic.to_string(self._global_frame_type[self.flag_opcode]),
            payload_length = self._payload_length,
            mask_key = False if self._mask_key is False else hex(
                self._mask_key).upper()
        )

    def __repr__(self):
        return self.__str__()


class WebSocketFrame(FrameBase):
    def __init__(self, raw_websocket):
        super(WebSocketFrame, self).__init__(packet.ByteArray(raw_websocket))


class FrameGenerator(FrameBase):
    def __init__(self):
        init_packet = packet.Packet(b'\x00\x00')
        super(FrameGenerator, self).__init__(init_packet)

        # first-byte information
        self._flag_fin = 1
        self._flag_rsv1 = 0
        self._flag_rsv2 = 0
        self._flag_rsv3 = 0

        # default is text-frame
        self._flag_opcode = 1

        # mask information
        self._flag_mask = 0
        self._mask_key = False

        # payload information
        self._payload_data = b''
        self._payload_length = 0
        self._flag_payload_length = 0

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

    def opcode(self, opcode):
        self._flag_opcode = opcode & 0xF
        return self

    def set_payload_data(self, contents):
        self._payload_data = generic.to_bytes(contents)
        self._payload_length = len(self._payload_data)
        if self._payload_length < 126:
            self._flag_payload_length = self._payload_length
        elif self._payload_length < 65536:
            self._flag_payload_length = 126
        else:
            self._flag_payload_length = 127
        return self


def _build_base_frame(from_client, extra_data):
    # create a frame
    rst_frame = FrameGenerator()
    # judge is client-to-server
    if from_client:
        rst_frame.set_mask_key(ws_utils.ws_generate_frame_mask_key())
    # add extra data
    if extra_data:
        rst_frame.set_payload_data(extra_data)
    return rst_frame


def generate_ping_frame(from_client=False, extra_data=None):
    # ping-frame opcode = 0x9
    return _build_base_frame(from_client, extra_data).opcode(0x9)


def generate_pong_frame(from_client=False, extra_data=None):
    # pong-frame opcode = 0xA
    return _build_base_frame(from_client, extra_data).opcode(0xA)


def generate_text_frame(text, from_client=False):
    # text-frame opcode = 0x1
    return _build_base_frame(from_client, text).opcode(0x1)


def generate_binary_frame(contents, from_client=False):
    # text-frame opcode = 0x1
    return _build_base_frame(from_client, contents).opcode(0x2)


def generate_binary_frame_from_file(path_to_file, from_client=False):
    # open file and read all contents
    with open(path_to_file, 'rb') as fd:
        buffer = fd.read(os.path.getsize(path_to_file))
        return generate_binary_frame(buffer, from_client)


def generate_close_frame(from_client=False, extra_data=None, errno=1000):
    errno = struct.pack('!h', errno)
    reason = generic.to_bytes('' if extra_data is None else extra_data)
    return _build_base_frame(from_client, errno + reason).opcode(0x8)


class TextMessage(object):
    def __init__(self, message, from_client=False):
        if not isinstance(message, (str, bytes)):
            raise TypeError('message must be str or bytes type')
        self._message = message
        self._from_client = from_client

    @property
    def generate_frame(self):
        return generate_text_frame(self._message, self._from_client)


class FileTextMessage(TextMessage):
    def __init__(self, file_name, from_client=False):
        try:
            with open(file_name, 'r') as fd:
                super(FileTextMessage, self).__init__(fd.read(), from_client)
        except Exception:
            raise


class BinaryMessage(TextMessage):
    def __init__(self, contents, from_client=False):
        if isinstance(contents, bytes):
            raise TypeError('binary frame must be bytes type')
        super(BinaryMessage, self).__init__(contents, from_client)

    @property
    def generate_frame(self):
        return generate_binary_frame(self._message, self._from_client)


class FileBinaryMessage(BinaryMessage):
    def __init__(self, file_name, from_client=False):
        try:
            with open(file_name, 'rb') as fd:
                super(FileBinaryMessage, self).__init__(fd.read(), from_client)
        except Exception:
            raise
