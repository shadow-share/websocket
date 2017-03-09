Apache Proxy 
---

### Enable Proxy
In `httpd.conf`

```

```

In `httpd-vhosts.conf`
```
<VirtualHost *:8080>
    DocumentRoot "path/to/document-root"
    ServerName [server_name]
    <Directory "path/to/document-root">
        Order deny,allow
        Deny from All
        Allow from All
    </Directory>

    # In Here
    ProxyPass /ws http://127.0.0.1:8999/  
    ProxyPassReverse /ws http://127.0.0.1:8999/
</VirtualHost>
```
