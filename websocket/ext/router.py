#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#
import re
from websocket.utils import (
    logger, exceptions
)


class Router(object):

    def __init__(self):
        self._default_dict = dict()
        self._route_tree = dict()  # type: dict

    def register_default(self, key, value):
        exceptions.raise_parameter_error('key', str, key)
        self._default_dict[key] = value

    def unregister_default(self, key):
        exceptions.raise_parameter_error('key', str, key)
        self._default_dict.pop(key)

    def register(self, url, key, value):
        exceptions.raise_parameter_error('url', str, url)
        exceptions.raise_parameter_error('key', str, key)
        if url in self._route_tree:
            self._route_tree[url][key] = value
        else:
            self._route_tree[url] = dict({key: value})

    def unregister(self, url, key=None):
        exceptions.raise_parameter_error('url', str, url)
        exceptions.raise_parameter_error('key', str, key)
        if url in self._route_tree:
            if key is None:
                self._route_tree[url].clear()
            else:
                self._route_tree[url].pop(key)
        else:
            raise exceptions.ParameterError('url not found in router')

    def solution(self, url, key=None):
        exceptions.raise_parameter_error('url', str, url)
        exceptions.raise_parameter_error('key', str, key)
        if url in self._route_tree:
            if key in self._route_tree[url]:
                return self._route_tree[url][key]
            elif key in self._default_dict:
                return self._default_dict[key]
        else:
            if key in self._default_dict:
                return self._default_dict[key]
        raise exceptions.ParameterError('url or key not found in router')

    @staticmethod
    def _parse_url(url: str):
        if not url.startswith('/'):
            url = '/' + url
        return re.subn('(/{2,})+', '/', url)
