#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#
import re
import abc
from collections import namedtuple
from websocket import utils

# Http version 1.1
HTTP_VERSION_1_1 = 1.1
# Http version 1.0
HTTP_VERSION_1_0 = 1.0

class HttpField(namedtuple('HttpField', 'key, value')):

    def __str__(self):
        return '<HttpField \'{}\' => \'{}\'>'.format(self.key, self.value)

    def __repr__(self):
        return '<HttpField \'{}\' => \'{}\'>'.format(self.key, self.value)

# Response status code description
_response_status_code_description = {
    101: b'Switching Protocols',
    200: b'OK', 201: b'Created', 202: b'Accepted',
    301: b'Moved Permanently', 302: b'Moved Permanently',
    400: b'Bad Request', 401: b'Unauthorized', 403: b'Forbidden',
    404: b'Not Found', 426: b'Upgrade Required',
    500: b'Internal Server Error'
}

# Http message base class
class HttpMessage(object, metaclass = abc.ABCMeta):

    def __init__(self):
        pass

    @staticmethod
    def factory(cls):
        pass

    @abc.abstractclassmethod
    def __str__(self):
        return ''

    def __repr__(self):
        return '<{} Hello World>'.format(self.__class__.__str__())


class HttpRequest(HttpMessage):

    def __init__(self):
        super(HttpRequest, self).__init__()

    def __str__(self):
        return 'HttpRequest'


class HttpResponse(HttpMessage):

    def __init__(self):
        super(HttpResponse, self).__init__()

    def __str__(self):
        return 'HttpResponse'


def is_http_protocol(raw_data):
    lines = utils.to_string(raw_data).split('\r\n')

    # request/response format
    if not re.match(r'(GET|POST|PUT|DELETE|UPDATE) ([\w\/\-_\.]+) HTTP\/(1\.0|1\.1)$', lines[0], re.I):
        if not re.match(r'HTTP\/(1\.0|1\.1) ([\d]+) ([\w\s]+)$', lines[0], re.I):
            return False

    # header-fields
    for field in lines[1:]:
        if not re.match(r'/([\w\-_]+)\s+:\s+([\w\-_]+)$/', field):
            return False

    # is http request/response
    return True


def create_http_request():
    pass


def create_http_response():
    pass
