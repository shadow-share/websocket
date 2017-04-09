#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#
import abc
from urllib import parse
from websocket.utils import generic, exceptions


class KeyValuePairs(object):
    """ A Key-Value Pairs

    :param self._key: Key in the key-value pairs
    :param self._index: Lowercase keys
    :param self._value: Value in the key-value pairs
    """

    def __init__(self, key: [bytes, str], value: [bytes, str]):
        self._key = generic.to_bytes(key)
        self._index = generic.to_bytes(key).lower()
        self._value = generic.to_bytes(value)

    def pack(self):
        return b': '.join([self._key, self._value])

    @property
    def key(self):
        return self._key

    @property
    def value(self):
        return self._value

    def __str__(self):
        return '<KeyValuePairs {} => {}>'.format(self._key, self._value)

    def __repr__(self):
        return self.__str__()


class HttpOptions(object):

    def __init__(self, *options, **kwargs):
        self._options = dict()
        self.update(*options, **kwargs)

    def get_value(self, key: [bytes, str], *, value_type=bytes):
        _kvp = self._options[generic.to_bytes(key).lower()]

        if _kvp:
            if value_type is str:
                return generic.to_string(_kvp.value)
            elif value_type is bytes:
                return _kvp.value
            else:
                raise exceptions.ParameterError(
                    'value type except str or bytes, got {}'.format(
                        value_type.__name__))
        return None

    def update(self, *options, **kwargs):
        for option in options:
            if isinstance(option, (list, tuple)):
                if len(option) == 2:
                    k = generic.to_bytes(option[0])
                    v = generic.to_bytes(option[1])
                    self._options.update({k.lower(): KeyValuePairs(k, v)})
                elif isinstance(option, KeyValuePairs):
                    self._options.update({option.key.lower(): option})
        for k, v in kwargs.items():
            k = generic.to_bytes(k)
            self._options.update({k.lower(): KeyValuePairs(k, v)})

    def pack(self):
        return b'\r\n'.join(map(lambda p: p.pack(), self._options.values()))

    def __contains__(self, key: [bytes, str]):
        key = generic.to_bytes(key).lower()
        return key in self._options

    def __len__(self):
        return len(self._options)

    def __getitem__(self, key: [bytes, str]):
        key = generic.to_bytes(key).lower()
        return self._options.get(key, None)

    def __str__(self):
        return self._dumps(self._options)

    @staticmethod
    def _dumps(_object: dict, indent: int = 1):
        rst = b'{\n'
        for k, v in _object.items():
            rst += (b'\t' * indent) + k + b': ' + v.value + b'\n'
        rst += b'}'
        return generic.to_string(rst)

    def __repr__(self):
        return self.__str__()


# Http version 1.0
HTTP_VERSION_1_0 = 0x0000
# Http version 1.1
HTTP_VERSION_1_1 = 0x0001
# Http GET method
HTTP_GET = b'GET'
# Http POST method
HTTP_POST = b'POST'
# Http PUT method
HTTP_PUT = b'PUT'
# Http DELETE method
HTTP_DELETE = b'DELETE'
# Http UPDATE method
HTTP_UPDATE = b'UPDATE'
# Http HEAD method
HTTP_HEAD = b'HEAD'
# Http methods
_http_methods = \
    [HTTP_GET, HTTP_POST, HTTP_PUT, HTTP_DELETE, HTTP_UPDATE, HTTP_HEAD]


class _HttpMessage(object, metaclass=abc.ABCMeta):
    def __init__(self, http_version, payload_data: [bytes, str], *options):
        self.header = HttpOptions(*options)

        if http_version not in [HTTP_VERSION_1_0, HTTP_VERSION_1_1]:
            raise exceptions.ParameterError('http version invalid')
        self.http_version = b'HTTP/1.' + \
                            b'1' if http_version is HTTP_VERSION_1_1 else b'0'
        self._payload_data = b'' if payload_data is None else payload_data
        self._payload_data = generic.to_bytes(self._payload_data)
        if len(self._payload_data):
            self.header.update(('Content-Length', len(self._payload_data)))

    @property
    def content_length(self):
        return len(self._payload_data)

    @abc.abstractclassmethod
    def pack(self):
        pass

    @abc.abstractclassmethod
    def __str__(self):
        pass

    @abc.abstractclassmethod
    def __repr__(self):
        pass


class HttpRequest(_HttpMessage):
    def __init__(self, method, url: [bytes, str], *options,
                 http_version=HTTP_VERSION_1_1, payload_data=None):
        super(HttpRequest, self).__init__(http_version, payload_data, *options)

        self._url_split_rst = parse.urlparse(url)
        self._request_url = generic.to_bytes(url)
        method = generic.to_bytes(method).upper()
        if method not in _http_methods:
            raise exceptions.ParameterError('method parameter invalid')
        self._http_method = method

    def pack(self):
        request_line = b' '.join(
            [self._http_method, self._request_url, self.http_version])
        return b'\r\n'.join(
            [request_line, self.header.pack(), b'', self._payload_data])

    def __str__(self):
        return "<HttpRequest method='{}' url='{}'>".format(
            generic.to_string(self._http_method),
            generic.to_string(self._request_url))

    def __repr__(self):
        return self.__str__()

    @property
    def url_scheme(self):
        return generic.to_string(self._url_split_rst.scheme)

    @property
    def url_netloc(self):
        return generic.to_string(self._url_split_rst.netloc)

    @property
    def url_path(self):
        return generic.to_string(self._url_split_rst.path)


_status_codes = {
    # Informational.
    100: b'Continue',
    101: b'Switching Protocols',
    200: b'Ok',

    # Client Error.
    400: b'Bad Request',
    401: b'Unauthorized',
    403: b'Forbidden',
    404: b'Not Found',
    405: b'Method Not Allowed',

    # Server Error.
    500: b'Internal Server Error',
    503: b'Service Unavailable',
    505: b'Http Version Not Supported',
}


class HttpResponse(_HttpMessage):
    def __init__(self, status_code, *options,
                 http_version=HTTP_VERSION_1_1, payload_data=None):
        super(HttpResponse, self).__init__(http_version, payload_data, *options)

        if not isinstance(status_code, int):
            raise exceptions.ParameterError(
                'status code except int, got {}'.format(type(status_code)))
        self._status_code = status_code
        self._description = _status_codes.get(self._status_code, b'')

    def pack(self):
        status_code = generic.to_bytes(self._status_code)
        response_line = b' '.join(
            [self.http_version, status_code, self._description])
        return b'\r\n'.join(
            [response_line, self.header.pack(), b'', self._payload_data])

    def __str__(self):
        return '<HttpResponse status={}>'.format(self._status_code)

    def __repr__(self):
        return self.__str__()


def factory_http_message(raw_http_message: bytes):
    if isinstance(raw_http_message, str):
        raw_http_message = generic.to_bytes(raw_http_message)
    if not isinstance(raw_http_message, bytes):
        raise exceptions.ParameterError('raw message except bytes type')

    if not raw_http_message.find(b'\r\n\r\n'):
        raise exceptions.ParameterError('raw message may not be complete')
    split_rst = raw_http_message.split(b'\r\n\r\n', 1)
    if len(split_rst) is 1:
        header, payload = split_rst[0], None
    else:
        header, payload = split_rst
    header_lines = header.split(b'\r\n')

    _http_options = []
    for option in header_lines[1:]:
        k, v = option.split(b':', 1)
        _http_options.append((k.strip(), v.strip()))

    a, b, c = header_lines[0].split(b' ', 2)
    # request or response
    if a in _http_methods:
        # raw message is http-request
        _http_version = \
            HTTP_VERSION_1_1 if c == b'HTTP/1.1' else HTTP_VERSION_1_0
        return HttpRequest(a, b, *_http_options,
                           http_version=_http_version,
                           payload_data=payload)
    else:
        # raw message is http-response
        _http_version = \
            HTTP_VERSION_1_1 if a == b'HTTP/1.1' else HTTP_VERSION_1_0
        return HttpResponse(int(b), *_http_options,
                            http_version=_http_version,
                            payload_data=payload)


if __name__ == '__main__':
    key_value_pairs = KeyValuePairs('key1', 'value1')
    assert key_value_pairs.key == b'key1'
    assert key_value_pairs.value == b'value1'
    assert key_value_pairs.pack() == b'key1: value1'

    ops = HttpOptions(('key1', 'value1'), ('key2', 'value2'))
    try:
        assert ops.pack() == b'key1: value1\r\nkey2: value2'
    except AssertionError:
        assert ops.pack() == b'key2: value2\r\nkey1: value1'
    assert 'key1' in ops
    assert 'KEY1' in ops

    req = HttpRequest('GET', '/url_path?query=value#frag=footer',
                      ('key1', 'value1'), ('key2', 'value2'), payload_data='+')
    print(req)
    print(req.pack())

    rsp = HttpResponse(
        200, ('key1', 'value1'), ('key2', 'value2'), payload_data=b'+')
    print(rsp)
    print(rsp.pack())

    msg0 = factory_http_message(req.pack())
    print(msg0)
    assert 'Content-Length' in msg0.header

    msg1 = factory_http_message(rsp.pack())
    print(msg1)
    assert 'Content-Length' in msg1.header
