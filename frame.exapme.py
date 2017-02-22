'''
Byte  0 * * * * * * * 1 * * * * * * * 2 * * * * * * * 3 * * * * * * * -
      |               |               |               |               |
bit   0               |   1           |       2       |           3   |
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


A single-frame unmasked text message

    0x81 0x05 0x48 0x65 0x6c 0x6c 0x6f

    [
        (1, 0, 0, 0, 0, 0, 0, 1), # FIN = 1, RSV1 = 0, RSV2 = 0, RSV3 = 0, opcode = 1(text frame)
        (0, 0, 0, 0, 0, 1, 0, 1), # MASK = 0, Payload_Len = 5(Server to Client, Payload len = 5bytes)
        (0, 1, 0, 0, 1, 0, 0, 0), # ASCII, H
        (0, 1, 1, 0, 0, 1, 0, 1), # ASCII, e
        (0, 1, 1, 0, 1, 1, 0, 0), # ASCII, l
        (0, 1, 1, 0, 1, 1, 0, 0), # ASCII, l
        (0, 1, 1, 0, 1, 1, 1, 1)  # ASCII, o
    ]


A single-frame masked text message

    0x81 0x85 0x37 0xfa 0x21 0x3d 0x7f 0x9f 0x4d 0x51 0x58

    [
        (1, 0, 0, 0, 0, 0, 0, 1), # FIN = 1, RSV1 = 0, RSV2 = 0, RSV3 = 0, opcode = 1(text frame)
        (1, 0, 0, 0, 0, 1, 0, 1), # MASK = 1, Payload_Len = 5
        (0, 0, 1, 1, 0, 1, 1, 1), # = 0x37
        (1, 1, 1, 1, 1, 0, 1, 0), # = 0xfa
        (0, 0, 1, 0, 0, 0, 0, 1), # = 0x21
        (0, 0, 1, 1, 1, 1, 0, 1), # = 0x3d      MASK_KEY = 0x37fa213d
        (0, 1, 1, 1, 1, 1, 1, 1), # = 0x7f      0x7f ^ 0x37 = 72, ASCII H
        (1, 0, 0, 1, 1, 1, 1, 1), # = 0x9f      0x9f ^ 0xfa = 101, ASCII e
        (0, 1, 0, 0, 1, 1, 0, 1), # = 0x4d      0x4d ^ 0x21 = 108, ASCII l
        (0, 1, 0, 1, 0, 0, 0, 1), # = 0x51      0x51 ^ 0x3d = 108, ASCII l
        (0, 1, 0, 1, 1, 0, 0, 0)  # = 0x85      0x58 ^ 0x37 = 111, ASCII o
    ]


A fragmented unmasked text message

    fragmented_1: 0x01 0x03 0x48 0x65 0x6c

    [
        (0, 0, 0, 0, 0, 0, 0, 1), # FIN = 0, RSV1 = 0, RSV2 = 0, RSV3 = 0, opcode = 1(text frame)
        (0, 0, 0, 0, 0, 0, 1, 1), # MASK = 0, Payload_Len = 3
        (0, 1, 0, 0, 1, 0, 0, 0), # ASCII H
        (0, 1, 1, 0, 0, 1, 0, 1), # ASCII e
        (0, 1, 1, 0, 1, 1, 0, 0)  # ASCII l
    ]

    fragmented_2: 0x80 0x02 0x6c 0x6f

    [
        (1, 0, 0, 0, 0, 0, 0, 0), # FIN = 1, RSV1 = 0, RSV2 = 0, RSV3 = 0, opcode = 1(continuation frame)
        (0, 0, 0, 0, 0, 0, 1, 0), # MASK = 0, Payload = 2
        (0, 1, 1, 0, 1, 1, 0, 0), # ASCII l
        (0, 1, 1, 0, 1, 1, 1, 1)  # ASCII o
    ]


Unmasked Ping request and masked Ping response

    0x89 0x05 0x48 0x65 0x6c 0x6c 0x6f

    [
        (1, 0, 0, 0, 1, 0, 0, 1), # FIN = 1, RSV1 = 0, RSV2 = 0, RSV3 = 0, opcode = 0x9(ping frame)
        (0, 0, 0, 0, 0, 1, 0, 1), # MASK = 0, Payload_Len = 5
        (0, 1, 0, 0, 1, 0, 0, 0), # ASCII, H
        (0, 1, 1, 0, 0, 1, 0, 1), # ASCII, e
        (0, 1, 1, 0, 1, 1, 0, 0), # ASCII, l
        (0, 1, 1, 0, 1, 1, 0, 0), # ASCII, l
        (0, 1, 1, 0, 1, 1, 1, 1)  # ASCII, o
    ]


256 bytes binary message in a single unmasked frame

    0x82 0x7E 0x0100 [256 bytes of binary data]

    [
        (1, 0, 0, 0, 0, 0, 1, 0), # FIN = 1, RSV1 = 0, RSV2 = 0, RSV3 = 0, opcode = 0x2(binary frame)
        (0, 1, 1, 1, 1, 1, 1, 0), # MASK = 0, Payload = 126
        (0, 0, 0, 0, 0, 0, 0, 1),
        (0, 0, 0, 0, 0, 0, 0, 0)  # (if payload len == 126)Extended payload length(16-bit) = 256
        ...                       # 256 bytes of binary data
    ]


64KiB binary message in a single unmasked frame

    0x82 0x7F 0x0000000000010000 [65536 bytes of binary data]

    [
        (1, 0, 0, 0, 0, 0, 1, 0), # FIN = 1, RSV1 = 0, RSV2 = 0, RSV3 = 0, opcode = 0x2(binary frame)
        (0, 1, 1, 1, 1, 1, 1, 1), # MASK = 0, Payload_Len = 127
        (0, 0, 0, 0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0, 0, 0, 1),
        (0, 0, 0, 0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0, 0, 0, 0)  # (if payload len == 127)Extended payload length(64-bit) = 65536
        ...                       # 65536 bytes of binary data
    ]

'''
