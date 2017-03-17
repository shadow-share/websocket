#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#
import argparse
from websocket import websocket_server, websocket_client

def _add_generic_options(parser:argparse.ArgumentParser):
    parser.add_argument('--version',
                        action = 'store_true',
                        help = 'dhow version information')
    parser.add_argument('-v', '--verbose',
                        action = 'count',
                        default = 0,
                        help = 'verbose level')

def client():
    print('Start Client')


def server():
    parser = argparse.ArgumentParser()

    parser.add_argument('-s', '--server',
                        default = 'localhost',
                        type = str,
                        help = 'server address')
    parser.add_argument('-p', '--port',
                        default = '8999',
                        type = int,
                        help = 'server listen port')
    parser.add_argument('-d', '--deamon',
                        type = str,
                        choices = [ 'start', 'stop', 'debug' ],
                        help = 'deamon mode')
    parser.add_argument('handler_file',
                        type = str,
                        help = 'handlers script')
    _add_generic_options(parser)
    options = parser.parse_args()
    print(options)

