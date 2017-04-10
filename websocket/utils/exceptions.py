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


def raise_parameter_error(name, except_type, got_val):
    if not isinstance(got_val, except_type):
        raise ParameterError(
            '{name} except {except_type}, got {got_type}'.format(
                name=name,
                except_type=except_type.__name__,
                got_type=type(got_val).__name__))


class ExitWrite(Exception):
    pass


class BroadcastError(Exception):
    pass


class HttpVerifierError(Exception):
    pass

