#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#
import sys

# Package name
PKG_NAME = 'websocket'
# Package version
VERSION = '0.0.1'
__version__ = VERSION


class VersionError(Exception):
    pass


if sys.version_info[0] < 3:
    raise VersionError('websocket package only run under the Python3.X')

