from constants import *
import traceback
import datetime
#import smbprotocol.execeptions

def log(e):
    with open("error.log", "a") as f:                                                              

        errorLines = traceback.format_exc()

        f.write(datetime.datetime.now().isoformat())
        f.write("\n")
        f.write(errorLines)
        print(errorLines)
        f.write("\n====================================\n")

        #if app.config["LOG_SERVER"]:
        #    notifications.sendError(e, errorLines, app)

    if (isinstance(e, BrokenPipeError)):
                # TODO fix this
                #or isinstance(e, smbprotocol.exceptions.LogonFailure)
                #or isinstance(e, smbprotocol.exceptions.SMBException)):
        return (WARNING_SAMBA_TICKET_EXPIRED, 500)
    else:
        return (WARNING_INTERNAL_SERVER_ERROR, 500)
