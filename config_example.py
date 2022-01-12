UPLOAD_FOLDER = "uploads/"
SECRET_KEY    = "SECRET"

SQLALCHEMY_DATABASE_URI = "sqlite:///database.sqlite"
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
NOTIFICATION_AUTH_PASS = ""

# local file id to authenticate with localfile:// runner #
# if this ID is set localfile-URLs will be generated #
LOCAL_FILE_ID = "NUMERIC_ID"