#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#
import sys

# Package name
PKG_NAME = 'websocket'
# Package version
PKG_VERSION = '0.0.1'

__doc__ = '''Websocket server and client write by python3

'''

class PythonVersionError(Exception):
    pass


if sys.version_info[0] < 3:
    raise PythonVersionError('websocket module only run under the python3+')

# import create server method
from websocket.server import *
# import logger
from websocket.utils import logger
# import all response type
from websocket.net.ws_frame import TextMessage, FileTextMessage, \
    BinaryMessage, FileBinaryMessage