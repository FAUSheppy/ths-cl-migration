UPLOAD_FOLDER = "uploads/"
SECRET_KEY    = "SECRET"

TMP_DIR = "tmp-files/"
BWA_FILE = "BWA 2022.xls"

SQLALCHEMY_DATABASE_URI = "sqlite:///database.sqlite"
SAMBA = False # enable samba clients
SMB_SERVER = "IP"
SMB_USER   = "user"
SMB_PASS   = "password"
SMB_SHARE  = "SHARE"
SMB_DRIVE  = "Drive the Samba-share is mounted as, if applicable, for example: 'T:'"

DOC_TEMPLATE_PATH = "document-templates"

# inbuildt notifications support https://github.com/FAUSheppy/signal-http-gateway/
SEND_NOTIFICATION   = False
NOTIFICATION_URL    = "URL"
NOTIFICATION_USERS  = ["USER_1", "USER_2"]
NOTIFICATION_AUTH_USER = "AUTH_USER"
NOTIFICATION_AUTH_PASS = "PASSWORD"

# local file id to authenticate with localfile:// runner #
# if this ID is set localfile-URLs will be generated #
LOCAL_FILE_ID = "NUMERIC_ID"

REPORTS_FILENAME_PREFIX = "Report-"
INVOICE_FILENAME_PREFIX = "Invoice-"

LOG_SERVER = "URL"
LOG_AUTH_USER = "AUTH_USER"
LOG_AUTH_PASS = "PASSWORD"

LOG_SERVICE = "service_name"
LOG_HOST = "hostname"

FILESYSTEM_PROJECTS_BASE_PATH = "/home/sheppy/THS_Proj/"
CLIENT_PATH_PREFIX = ""
