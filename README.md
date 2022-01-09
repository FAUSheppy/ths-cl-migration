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
| SMB_DRIVE | Samba drive name if mounted on a windows system |
| DOC_TEMPLATE_PATH | Path where docx-document templates are stored |
| SEND_NOTIFICATION | Should a notification be send on change or new entry |
| NOTIFICATION_URL | Gateway url to query |
| NOTIFICATION_USERS | List of users to send messages to (if gateway supports it) |
| NOTIFICATION_AUTH_USER | Gateway authentification user |
| NOTIFICATION_AUTH_PASS | Gateway authentification password |

# Windows

- install psql-odbc driver (32/64bit both)
- use OBDC-Administration app to add both drivers and the server connection

# Document Templates Config
Server will read a json file called *templates.json* in the configured templates directory which must have the following structure:

    {
        "template_name.docx" : {
                "description" : "Long description",
        }
        "template_name_2.docx" : {
                "description" : "Long description_2",
        }

        ...
    }

# Database Setup
If you are using sqlite you don't have to do anything. If you are using postgresql, create a user and database and change the variables in *config.py* accordingly.

# Modify Fields for documents
If you need to modify the input fields for your MS-Word document's mail-merge, you are best served using postgres and leveraging the amazing abilities of it's functionality by creating a special **VIEW**.
For example if you want to split off the start of your *projectId*-field, you can create a view like this:

    CREATE VIEW view_name AS
        SELECT cl.*,
                substring(cl.projectid::varchar(30) from 5 for 4) AS projectid_short
        FROM contract_locations cl;

    GRANT SELECT ON view_name TO username;

... and then reference this view and it's newly create field "projectid_short" in your document.

# Icinga Monitoring
The project contains the script *external_monitoring.py*, this script can be use in conjuncting with the [Icinga Async Monitoring Project](https://github.com/FAUSheppy/icinga-webhook-gateway), refer to its README for more information.

    Usage: external_monitoring.py [-h] [--url URL]
                                  [--monitoring-server MONITORING_SERVER]
                                  [--monitoring-token MONITORING_TOKEN]
                                  [--service-name SERVICE_NAME]
                                  [--project-id PROJECT_ID]
    
    optional arguments:
      -h, --help            show this help message and exit
      --url URL             Interface to target for check
      --monitoring-server   Monitoring Server
      --monitoring-token    Token for Monitoring Server
      --service-name        Service Name to submit as
      --project-id          A existing project-id to check


# Wishlist

- implement database consitency check (sheppy)
- implement carddav (contacts) integration (ths)
- advanced options when creating documents (e.g. actual invoice options) (ths)
- implement extended validation form main data entry form (sheppy)

---

This project aims to create a pipeline to migrate away from this obsolete technology, and use a real database and easy to use web-interface.
