# Migration Tool for docx-Databases
In the early 2000s it used to be common to use a database function in the doc/docx document-standard as source for data in MS-Office macro. For example, maintain a list of customers in such a "database" and use it to automatically populate letters and invoices based on project id's.

Now this approach has various drawbacks, including:

- it's incredibly slow
- it's loaded to memory in whole every time it's used
- newer MS-Office version don't allow you to use it over the network by default
- it's hard to maintain
- it does not support advanced queries

# Gateway Configuration
If you want to use the notification gateway, you can use the [signal-gateway](https://github.com/FAUSheppy/signal-http-gateway) behind nginx (for authentification).

    server {
        listen 443 ssl;
        server_name _;
    
        location / {
            auth_basic "Signal Gateway Auth";
            auth_basic_user_file "/path/to/auth/file";
            proxy_pass http://localhost:PORT;
        }
    
    }

# Configuration

| Key       | Description |
| --------- | ----------- |
| UPLOAD_FOLDER | Directory for uploads |
| SECRET_KEY | Secret key for WTF-forms |
| SQLALCHEMY_DATABASE_URI | Database to use |
| SMB_SERVER | Local Network Samba Server (optional) |
| SMB_USER | Samba User (required if samba server is defined)| 
| SMB_PASS | Samba Password (required if samba server is defined)| 
| SMB_SHARE | Samba Share (required if samba server is defined) |
| DOC_TEMPLATE_PATH | Path where docx-document templates are stored |
| SEND_NOTIFICATION | Should a notification be send on change or new entry |
| NOTIFICATION_URL | Gateway url to query |
| NOTIFICATION_USERS | List of users to send messages to (if gateway supports it) |
| NOTIFICATION_AUTH_USER | Gateway authentification user |
| NOTIFICATION_AUTH_PASS | Gateway authentification password |

# Windows

- install psql-odbc driver (32/64bit both)
- use OBDC-Administration app to add both drivers and the server connection

---

This project aims to create a pipeline to migrate away from this obsolete technology, and use a real database and easy to use web-interface.
