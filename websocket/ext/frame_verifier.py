#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#
from websocket.net import ws_frame
from websocket.utils import (
    logger, exceptions
)


class FrameVerifier(object):

    def __init__(self, client_name):
        self._client_name = client_name

    def verify_frame(self, frame: ws_frame.FrameBase):
        # MUST be 0 unless an extension is negotiated that defines meanings
        # for non-zero values.  If a nonzero value is received and none of
        # the negotiated extensions defines the meaning of such a nonzero
        # value, the receiving endpoint MUST _Fail the WebSocket
        # Connection_.
        if frame.flag_rsv1 or frame.flag_rsv2 or frame.flag_rsv3:
            logger.info('{} send frame invalid'.format(self._client_name))
            return False

        # As control frames cannot be fragmented, an intermediary MUST NOT
        # attempt to change the fragmentation of a control frame.
        if frame.flag_opcode >= 8 and frame.flag_fin != 1:
            logger.info('{} send frame invalid'.format(self._client_name))
            return False

        # All control frames MUST have a payload length of 125 bytes or less
        # and MUST NOT be fragmented.
        if frame.flag_opcode >= 0x08 and frame.payload_data_length > 125:
            logger.info('{} send frame invalid'.format(self._client_name))
            return False

        # An unfragmented message consists of a single frame with the FIN
        # bit set and an opcode other than 0.
        if frame.flag_fin == 1 and frame.flag_opcode == 0:
            logger.info('{} send frame invalid'.format(self._client_name))
            return False

        # a client MUST mask all frames that it sends to the server. The server
        # MUST close the connection upon receiving a frame that is not masked.
        if frame.flag_mask == 1 and frame.mask_key is False:
            # In this case, a server MAY send a Close frame with a status code
            # of 1002
            logger.info('{} send frame invalid'.format(self._client_name))
            return False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type or exc_tb:
            raise exc_val


def verify_frame(client_name, frame):
    try:
        with FrameVerifier(client_name) as verifier:
            return verifier.verify_frame(frame)
    except exceptions.FrameVerifierError:
        return False
