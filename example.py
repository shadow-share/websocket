#!/usr/bin/env python3
#
# Copyright (C) 2017 ShadowMan
#
import os
import sys
import random
import socket
import struct
from websocket import http

# ws_server = websocket_server.create_websocket_server(host = '127.0.0.1', port = 8999)
#
# ws_server.run_forever()


a = http.HttpRequest(http.HTTP_METHOD_GET, '/index.php', http.create_header_field('Accept', '*/*'))
print(a)
print(a.pack())
print(a['Accept'])

b = http.HttpResponse(200, http.create_header_field('Accept', '*/*'))
print(b)
print(b.pack())
print(b['Accept'])

t1 = a.pack()
t2 = b.pack()

print(http.is_http_protocol(t1))
print(http.is_http_protocol(t2))

print(http.factory(t1))
print(http.factory(t2))

t3 = '''HTTP/1.1 200 OK\r\n\
Server: bfe/1.0.8.18\r\n\
Date: Fri, 03 Mar 2017 08:34:26 GMT\r\n\
Content-Type: text/html;charset=utf-8\r\n\
Transfer-Encoding: chunked\r\n\
Connection: keep-alive\r\n\
Vary: Accept-Encoding\r\n\
Cache-Control: private\r\n\
Expires: Fri, 03 Mar 2017 08:34:26 GMT\r\n\
Content-Encoding: gzip\r\n\
Set-Cookie: __bsi=18287620895774850847_00_0_I_R_47_0303_C02F_N_I_I_0; expires=Fri, 03-Mar-17 08:34:31 GMT; domain=www.baidu.com; path=/\r\n\r\n'''

print(http.is_http_protocol(t3))
print(http.factory(t3))
print(http.factory(t3)['Set-Cookie'])

t4 = '''GET /home/xman/data/tipspluslist?indextype=manht&_req_seqid HTTP/1.1\r\n\
Host: www.baidu.com\r\n\
Connection: keep-alive\r\n\
Pragma: no-cache\r\n\
Cache-Control: no-cache\r\n\
Accept: text/plain, */*; q=0.01\r\n\
X-Requested-With: XMLHttpRequest\r\n\
User-Agent: Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36\r\n\
Referer: https://www.baidu.com/\r\n\
Accept-Encoding: gzip, deflate, sdch, br\r\n\
Accept-Language: zh-CN,zh;q=0.8\r\n\
Cookie: BAIDUID=166248C91015CA02981C010CB56F6311:FG=1;e=1; ORIGIN=2; bdime=0\r\n\r\n'''
print(http.is_http_protocol(t4))
print(http.factory(t4))
print(http.factory(t4)['Cookie'])