#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#

class FatalError(Exception):
    pass


class FrameHeaderParseError(Exception):
    pass


class ConnectClosed(Exception):
    pass


class RequestError(Exception):
    pass


class LoggerWarning(RuntimeWarning):
    pass


class DeamonError(Exception):
    pass


class SendDataPackError(Exception):
    pass


class InvalidResponse(Exception):
    pass


class ParameterError(Exception):
    pass

