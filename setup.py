#!/usr/bin/env python
#
# Copyright (C) 2017 ShadowMan
#
from setuptools import setup
from websocket import PKG_NAME, VERSION

setup(
    name = PKG_NAME,
    version = VERSION,
    description = 'websocket server and client by python',
    packages = [ 'websocket' ],
    entry_points={
        'console_scripts': [
            'wsclient = websocket.shell:client',
            'wsserver = websocket.shell:server'
        ],
    }
)
