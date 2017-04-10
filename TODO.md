TODO list for websocket develop
-------------------------------

websocket develop note

## SERVER

### XXX

 * connection close-information

 * Http Verify and WS-Handshake frame verify

### Fix Bugs

 * 


### Feature

 * timeout attrib

    connection timeout

    * server send close-frame, wait client send FIN


 * http-headers verifier

    eg. host, origin, etc.


 * encrypt message ?
    
    eg. sha1(md5(SECRET) + timestamp) + Encrypt(message, SECRET)
        
    * SECRET from user input
    
 
 * fragment frame
 
    eg. fragment-1: FIN = 0, opcode = 1
        fragment-2: FIN = 0, opcode = 0
        fragment-3: FIN = 1, opcode = 0 
   
   
### Module

 * Protocols Module

    ```python
    @register_ws_protocol('chat')
    @add_url_rule('/chat')
    class ChatHandler(WebsocketHandlerProtocol):
        
        def __init__(self):
            pass
        
    ```

 * Extensions Module

    ```python
    @add_url_rule('/chat')
    @enable_extension('permessage-deflate')
    class ChatHandler(WebsocketHandlerProtocol):
        
        def __init__(self):
            pass
        
    ```

 * Websocket Version Module

    ```python
    @add_url_rule('/chat')
    @register_ws_version('127')
    class ChatHandler(WebsocketHandlerProtocol):
        
        def __init__(self):
            pass
    ```
 
 * Websocket Frame opcode register 
 
 * wss Server

## Client

### Feature

 * Customer request header
 
 * register protocol/version/...
 