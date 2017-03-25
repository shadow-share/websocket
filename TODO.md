TODO list for websocket develop
-------------------------------

### XXX

 * connection close-information


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
    
    
### Module

 * Router Module
    ```python
    @add_url_rule('/chat')
    class ChatHandler(WebsocketHandlerProtocol):
        
        def __init__(self):
            pass
        
    ```

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