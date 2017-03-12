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
import socket
import struct
import logging
from websocket import utils, exceptions, websocket_utils


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
    for index, value in enumerate(utils.to_bytes(data)):
        transformed_string += struct.pack('!B', (value ^ mask_key_octet[index % 4]) & 0xff)
    return transformed_string


def parse_frame_length(frame_header):
    if not isinstance(frame_header, (str, bytes)):
        raise KeyError('frame_header must be str or bytes type')
    octet_array = utils.string_to_octet_array(frame_header)
    if len(octet_array) < 2:
        logging.warning('receive less than 2-bytes, octets={}'.format(octet_array))
        raise RuntimeError('frame header less than 2-bytes')

    # first bit is MASK flag
    payload_length = utils.octet_to_number(octet_array[1][1:])
    # if 0-125, that is the payload length
    if payload_length <= 125:
        # if frame is client-to-server, payload length does not include mask-key(4-byte)
        if octet_array[1][0] is 1:
            return len(octet_array), payload_length + 6
        return len(octet_array), payload_length + 2
    # If 126, the following 2 bytes interpreted as a
    # 16-bit unsigned integer are the payload length
    elif payload_length == 126:
        # Payload length field is in [2-4)bytes
        if len(octet_array) < 4:
            raise exceptions.FrameHeaderParseError(
                'payload length flag is 126, but header length is {}'.format(len(octet_array))
            )
        if octet_array[1][0] is 1:
            return len(octet_array), utils.octet_to_number(utils.flatten_list(octet_array[2:4])) + 8
        return len(octet_array), utils.octet_to_number(utils.flatten_list(octet_array[2:4])) + 4
    # If 127, the following 8 bytes interpreted as a
    # 64-bit unsigned integer (the most significant bit
    # MUST be 0) are the payload length.
    elif payload_length == 127:
        # Payload length field is in [2-10)bytes
        if len(octet_array) < 10:
            raise exceptions.FrameHeaderParseError(
                'payload length flag is 127, but header length is {}'.format(len(octet_array))
            )
        if octet_array[1][0] is 1:
            return len(octet_array), utils.octet_to_number(utils.flatten_list(octet_array[2:4])) + 14
        return len(octet_array), utils.octet_to_number(utils.flatten_list(octet_array[2:4])) + 10
    raise exceptions.FatalError('internal error')


def receive_single_frame(socket_fd):
    if not isinstance(socket_fd, socket.socket):
        raise KeyError('socket_fd must be socket.socket instance')
    # if frame is server send to client, and Payload_length = 127.
    # then this frame header is 10-bytes. Or less
    frame_contents = socket_fd.recv(10)
    received_length = frame_length = len(frame_contents)
    try:
        received_length, frame_length = parse_frame_length(frame_contents)
    except exceptions.FrameHeaderParseError as e:
            raise
    while len(frame_contents) < frame_length:
        frame_contents += socket_fd.recv(frame_length - received_length)
        received_length = len(frame_contents)
    return frame_contents


# using for judge frame type
Text_Frame = b'Text Frame'
Binary_Frame = b'Binary Frame'

class Frame_Base(object, metaclass = abc.ABCMeta):

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

    def __init__(self, raw_frame_bit_array):
        if len(raw_frame_bit_array) % 8 != 0:
            raise RuntimeError('the raw frame bit array is invalid')
        self._octet_array = utils.bit_array_to_octet_array(raw_frame_bit_array)
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
        self._flag_fin = self._octet_array[0][0]
        self._flag_rsv1 = self._octet_array[0][1]
        self._flag_rsv2 = self._octet_array[0][2]
        self._flag_rsv3 = self._octet_array[0][3]
        self._flag_opcode = utils.octet_to_number(self._octet_array[0][4:])
        # second byte(8-bits)
        # +-+-------------+
        # |M| Payload len |
        # |A|     (7)     |
        # |S|             |
        # |K|             |
        # +-+-+-+-+-------+
        self._flag_mask = self._octet_array[1][0]
        self._flag_payload_length = utils.octet_to_number(self._octet_array[1][1:])
        self._payload_length = self._flag_payload_length

        _last_byte_index = 2
        if self._payload_length is 126:
            # If 126, the following 2 bytes interpreted as a
            # 16-bit unsigned integer are the payload length
            self._payload_length = utils.octet_to_number(utils.flatten_list(self._octet_array[_last_byte_index:4]))
            _last_byte_index = 4
        elif self._payload_length is 127:
            # If 127, the following 8 bytes interpreted as a
            # 64-bit unsigned integer (the most significant bit
            # MUST be 0) are the payload length.
            self._payload_length = utils.octet_to_number(utils.flatten_list(self._octet_array[_last_byte_index:10]))
            _last_byte_index = 10

        # Masking-key, if MASK set to 1
        if self._flag_mask is 1:
            self._mask_key = utils.octet_to_number(
                utils.flatten_list(self._octet_array[_last_byte_index:_last_byte_index + 4])
            )
            _last_byte_index += 4
        else:
            self._mask_key = False

        # Payload Data
        self._payload_data = utils.octet_array_to_string(self._octet_array[_last_byte_index:])
        if self._flag_mask is 1:
            self._payload_data = ws_transform_payload_data(self._payload_data, self._mask_key)


    def pack(self):
        header_octet_array = []
        # first-byte
        header_octet_array.append((
            self._flag_fin, # FIN flag
            self._flag_rsv1, # RSV1 flag
            self._flag_rsv2, # RSV2 flag
            self._flag_rsv3, # RSV3 flag
            *utils.number_to_bit_array(self._flag_opcode)[::-1][4:] # Opcode
        ))
        # second-byte
        header_octet_array.append((
            self._flag_mask, # Mask flag
            *utils.number_to_bit_array(self._flag_payload_length)[::-1][1:] # Payload length flag [ <125, 126, 127 ]
        ))
        # payload_length
        if self._flag_payload_length is 126:
            header_octet_array.extend(utils.bit_array_to_octet_array(
                utils.number_to_bit_array(self._payload_length, 2), True),
            )
        elif self._flag_payload_length is 127:
            header_octet_array.extend(utils.bit_array_to_octet_array(
                utils.number_to_bit_array(self._payload_length, 8), True)
            )
        # Masking key
        if self._flag_mask is 1:
            _masking_key = struct.pack('!I', self._mask_key)
        else:
            _masking_key = b''
        # Payload data
        if self._flag_mask is 1:
            _payload_data = ws_transform_payload_data(self._payload_data, self._mask_key)
            return utils.octet_array_to_string(header_octet_array) + _masking_key + _payload_data
        return utils.octet_array_to_string(header_octet_array) + _masking_key + self._payload_data


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
            type = utils.to_string(self._global_frame_type[self.flag_opcode]),
            payload_length = self._payload_length,
            mask_key = False if self._mask_key is False else hex(self._mask_key).upper()
        )

    def __repr__(self):
        return self.__str__()


class Frame_Parser(Frame_Base):

    def __init__(self, socket_fd):
        bit_array = utils.string_to_bit_array(receive_single_frame(socket_fd))
        super(Frame_Parser, self).__init__(bit_array)


class Frame_Generator(Frame_Base):

    def __init__(self):
        super(Frame_Generator, self).__init__([ 0 ] * 16) # 2-bytes

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
        self._payload_data = utils.to_bytes(contents)
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
    rst_frame = Frame_Generator()
    # judge is client-to-server
    if from_client:
        rst_frame.set_mask_key(websocket_utils.ws_generate_frame_mask_key())
    # add extra data
    if extra_data:
        rst_frame.set_payload_data(extra_data)
    return rst_frame


def generate_ping_frame(from_client = False, extra_data = None):
    # ping-frame opcode = 0x9
    return _build_base_frame(from_client, extra_data).opcode(0x9)


def generate_pong_frame(from_client = False, extra_data = None):
    # pong-frame opcode = 0xA
    return _build_base_frame(from_client, extra_data).opcode(0xA)


def generate_text_frame(text, from_client = False):
    # text-frame opcode = 0x1
    return _build_base_frame(from_client, text).opcode(0x1)


def generate_binary_frame(contents, from_client = False):
    # text-frame opcode = 0x1
    return _build_base_frame(from_client, contents).opcode(0x2)


def generate_binary_frame_from_file(path_to_file, from_client = False):
    # open file and read all contents
    with open(path_to_file, 'rb') as fd:
        buffer = fd.read(os.path.getsize(path_to_file))
        return generate_binary_frame(buffer, from_client)


class TextMessage(object):

    def __init__(self, message, from_client = False):
        if not isinstance(message, (str, bytes)):
            raise TypeError('message must be str ot bytes type')
        self._message = message
        self._from_client = from_client


    @property
    def message(self):
        return generate_text_frame(self._message, self._from_client)


    @message.setter
    def message(self, message):
        if not isinstance(message, (str, bytes)):
            raise TypeError('message must be str ot bytes type')
        self._message = message


class FileTextMessage(TextMessage):

    def __init__(self, file_name, from_client = False):
        try:
            with open(file_name, 'r') as fd:
                buffer = fd.read(os.path.getsize(file_name))
                super(FileTextMessage, self).__init__(buffer, from_client)
        except Exception:
            raise


class BinaryMessage(TextMessage):

    def __init__(self, contents, from_client = False):
        super(BinaryMessage, self).__init__(contents, from_client)


    @property
    def message(self):
        return generate_binary_frame(self._message, self._from_client)


class FileMessage(BinaryMessage):

    def __init__(self, file_name, from_client = False):
        try:
            with open(file_name, 'rb') as fd:
                buffer = fd.read(os.path.getsize(file_name))
                super(FileMessage, self).__init__(buffer, from_client)
        except Exception:
            raise

