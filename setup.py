#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#
from setuptools import setup
from websocket import PKG_NAME, PKG_VERSION

setup(
    name = PKG_NAME,
    version = PKG_VERSION,
    description = 'websocket server and client by python',
    packages = [ 'websocket', 'websocket.utils' ]
)
