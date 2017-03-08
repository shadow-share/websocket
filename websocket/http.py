#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#
import re
import abc
from collections import namedtuple, OrderedDict
from websocket import utils


# Http version 1.1
HTTP_VERSION_1_1 = 1.1
# Http version 1.0
HTTP_VERSION_1_0 = 1.0

# Response status code description
_response_status_description = {
    101: b'Switching Protocols',
    200: b'OK', 201: b'Created', 202: b'Accepted',
    301: b'Moved Permanently', 302: b'Moved Permanently',
    400: b'Bad Request', 401: b'Unauthorized', 403: b'Forbidden',
    404: b'Not Found', 426: b'Upgrade Required',
    500: b'Internal Server Error'
}

# Http methods
HTTP_METHODS = [b'GET', b'POST', b'PUT', b'DELETE', b'UPDATE', b'HEAD']
# GET
HTTP_METHOD_GET = b'GET'
# POST
HTTP_METHOD_POST = b'POST'
# PUT
HTTP_METHOD_PUT = b'PUT'
# DELETE
HTTP_METHOD_DELETE = b'DELETE'
# UPDATE
HTTP_METHOD_UPDATE = b'UPDATE'
# HEAD
HTTP_METHOD_HEAD = b'HEAD'

class HttpField(namedtuple('HttpField', 'key value')):

    def __str__(self):
        return '<HttpField {} => {}>'.format(self.key, self.value)

    def __repr__(self):
        return '<HttpField {} => {}>'.format(self.key, self.value)

    def to_byte_string(self, crlf = True):
        return self.key + b' '.join([b':', self.value]) + b'\r\n'


# Http message base class
class HttpMessage(object, metaclass = abc.ABCMeta):

    def __init__(self, *header_fields):
        self._header_fields = OrderedDict()

        for k, v in filter(lambda el: isinstance(el, HttpField), header_fields):
            self._header_fields[utils.to_bytes(k)] = HttpField(utils.to_bytes(k), utils.to_bytes(v))

    @abc.abstractclassmethod
    def __str__(self):
        return RuntimeError('Derived class must be defined __str__ method')

    @abc.abstractclassmethod
    def pack(self):
        return RuntimeError('Derived class must be defined pack method')

    def __getitem__(self, item):
        return self._header_fields.get(utils.to_bytes(item))

    def __setitem__(self, key, value):
        self._header_fields[utils.to_bytes(key)] = utils.to_bytes(value)

    def __repr__(self):
        return '<{} Hello World>'.format(self.__class__.__str__())


class HttpRequest(HttpMessage):

    def __init__(self, request_method, request_resource, *header_field, http_version = HTTP_VERSION_1_1, extra_data = None):
        super(HttpRequest, self).__init__(*header_field)

        if isinstance(request_method, (str, bytes)):
            self._request_method = utils.to_bytes(request_method.upper())

            if self._request_method not in HTTP_METHODS:
                raise KeyError('the request method \'{}\' is invalid'.format(request_method))
        else:
            raise TypeError('request method must be str or bytes type')

        if not isinstance(request_resource, (str, bytes)):
            raise TypeError('request resource must be str or bytes type')
        self._request_resource = utils.to_bytes(request_resource)

        if http_version not in (HTTP_VERSION_1_1, HTTP_VERSION_1_0):
            raise TypeError('http version invalid')
        self._http_version = b'HTTP/1.1' if http_version == HTTP_VERSION_1_1 else b'HTTP/1.0'

        if extra_data is None:
            self._extra_data = b''
        else:
            if not isinstance(extra_data, (str, bytes)):
                raise TypeError('extra data must be str or bytes type')
            self._extra_data = utils.to_bytes(extra_data)

    def __str__(self):
        return '<HttpRequest method={method} resource={resource} version={version} fields-length={fields_length}>'.format(
            method = self._request_method,
            resource = self._request_resource,
            version = self._http_version,
            fields_length = len(self._header_fields)
        )

    def pack(self):
        bytes_string_rst = b''

        # first-line
        # FORMAT: [Method] [Resource] [Version]\r\n
        bytes_string_rst += b' '.join([ self._request_method, self._request_resource, self._http_version ])
        bytes_string_rst += b'\r\n'

        # header-field
        # FORMAT: [Key]: [Value]\r\n
        for http_field in self._header_fields:
            bytes_string_rst += self._header_fields[http_field].to_byte_string()
        # In header of end
        bytes_string_rst += b'\r\n'

        # Extra data
        bytes_string_rst += self._extra_data

        return bytes_string_rst

    @property
    def method(self):
        return self._request_method

    @property
    def resource(self):
        return self._request_resource

    @property
    def http_version(self):
        return self._http_version

    @property
    def payload_data(self):
        return self._extra_data


class HttpResponse(HttpMessage):

    def __init__(self, status_code, *header_field, http_version = HTTP_VERSION_1_1, description = None, extra_data = None):
        super(HttpResponse, self).__init__(*header_field)

        if isinstance(status_code, (str, bytes)):
            status_code = int(status_code)
        elif not isinstance(status_code, int):
            raise TypeError('status_code must be int type')

        if description is not None:
            if not isinstance(description, (str, bytes)):
                raise TypeError('code description must be str or bytes type')

        if status_code in _response_status_description:
            self._status_code = utils.to_bytes(str(status_code))
            self._description = _response_status_description[status_code] if description is None else description
        else:
            raise KeyError('must be provide code\'{}\' description'.format(status_code))

        if http_version not in (HTTP_VERSION_1_1, HTTP_VERSION_1_0):
            raise TypeError('http version invalid')
        self._http_version = b'HTTP/1.1' if http_version == HTTP_VERSION_1_1 else b'HTTP/1.0'

        if extra_data is None:
            self._extra_data = b''
        else:
            if not isinstance(extra_data, (str, bytes)):
                raise TypeError('extra data must be str or bytes type')
            self._extra_data = utils.to_bytes(extra_data)


    def __str__(self):
        return '<HttpResponse code={code} description={description} version={version} fields-length={fields_length}>'.format(
            code = self._status_code,
            description = self._description,
            version = self._http_version,
            fields_length = len(self._header_fields)
        )

    def pack(self):
        bytes_string_rst = b''

        # first-line
        # FORMAT: [Version] [Code] [Description]\r\n
        bytes_string_rst += b' '.join([ self._http_version, self._status_code, self._description ])
        bytes_string_rst += b'\r\n'

        # header-field
        # FORMAT: [Key]: [Value]\r\n
        for http_field in self._header_fields:
            bytes_string_rst += self._header_fields[http_field].to_byte_string()
        # In header of end
        bytes_string_rst += b'\r\n'

        # Extra data
        bytes_string_rst += self._extra_data

        return bytes_string_rst

    @property
    def version(self):
        return self._http_version

    @property
    def status_code(self):
        return self._status_code

    @property
    def description(self):
        return self._description

    @property
    def payload_data(self):
        return self._extra_data


def is_http_protocol(raw_data):
    lines = list(filter(lambda l: l, utils.to_string(raw_data).split('\r\n')))

    # request/response format
    if not re.match(r'(GET|POST|PUT|DELETE|UPDATE|HEAD) (.*) HTTP\/(1\.0|1\.1)$', lines[0], re.I):
        if not re.match(r'HTTP\/(1\.0|1\.1) ([\d]+) ([\w\s]+)$', lines[0], re.I):
            return False

    # header-fields
    for line in lines[1:]:
        if not re.match(r'([\w\-_]+)\s*:\s*(.*)$', line, re.I):
            return False

    # is http request/response
    return True


def create_header_field(key, value):
    return HttpField(key, value)


def create_header_fields(*fields):
    return [ HttpField(*field) for field in fields ]


def factory(raw_data):
    header, payload_data = utils.to_string(raw_data).split('\r\n\r\n', 2)

    if not is_http_protocol(header):
        raise RuntimeError('the data Does not appear to be a valid HTTP data')

    header_line = list(filter(lambda l: l, utils.to_string(header).split('\r\n')))
    first_line = header_line[0].split(' ', 3)

    header_fields = []
    for line in header_line[1:]:
        k, v = line.split(':', 1)
        header_fields.append(HttpField(k.strip(), v.strip()))

    if re.match(r'(GET|POST|PUT|DELETE|UPDATE|HEAD)', first_line[0]):
        method = first_line[0].strip().upper()
        resource = first_line[1].strip()
        version = first_line[2].strip().upper()

        return HttpRequest(method, resource, *header_fields,
                           http_version = _version_check(version),
                           extra_data = payload_data)
    else:
        # Response Frame
        version = first_line[0].strip().upper()
        code = first_line[1].strip()
        description = first_line[2].strip()

        return HttpResponse(int(code), *header_fields,
                            http_version = _version_check(version),
                            description = description,
                            extra_data = payload_data)

def _version_check(version_string):
    if version_string == 'HTTP/1.1':
        return HTTP_VERSION_1_1
    elif version_string == 'HTTP/1.0':
        return HTTP_VERSION_1_0
