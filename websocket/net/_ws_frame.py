#!/usr/bin/env python
#
# Copyright (C) 2017
#
'''
typedef struct _websocket_frame {
    struct _first_byte {
        unsigned fin               : 1;
        unsigned rsv1              : 1;
        unsigned rsv2              : 1;
        unsigned rsv3              : 1;
        unsigned opcode            : 4;
    } first;
    struct _second_byte {
        unsigned mask              : 1;
        unsigned payload_length    : 7;
    } second;
    union extension_payload_length {
        struct {
            unsigned b0                : 8;
            unsigned b1                : 8;
            unsigned b2                : 8;
            unsigned b3                : 8;
            unsigned b4                : 8;
            unsigned b5                : 8;
            unsigned b6                : 8;
            unsigned b7                : 8;
        } bytes;
        unsigned long long value; 
    } extension_payload_length;
    unsigned mask_key;
} WebSocketFrame;

'''