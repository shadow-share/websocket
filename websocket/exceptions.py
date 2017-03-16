#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#

class FatalError(Exception):
    pass


class FrameHeaderParseError(Exception):
    pass


class ConnectCLosed(Exception):
    pass


class RequestError(Exception):
    pass


class LoggerWarning(RuntimeWarning):
    pass