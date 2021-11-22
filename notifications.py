import requests
import Constants
from requests.auth import HTTPBasicAuth

def makeRepresentation(oldCl, oldAd, cl, ad):
    dates = ad.dates

    contentString = ""

    if not oldCl:
        startString = "Neuer Eintrag: {}\n".format(cl.projectId)
    else:
        startString = "Änderung von Eintrag: {}".format(oldCl.projectId)

    for key in cl.toDict():
        if not oldCl:
            contentString += "{}: {}\n".format(COLS_TO_DISPLAY_NAME[key], cl[key])
        elif: cl[key] != oldCl[key]:
            contentString += "{}: {} -> {}\n".format(COLS_TO_DISPLAY_NAME[key], oldCl[key], cl[key])
        else:
            continue

    
    if not oldAd and ad.dates:
        contentString

    return startString +  contentString

def sendSignal(content, app):

    url      = app.config["NOTIFICATION_URL"]
    users    = app.config["NOTIFICATION_USERS"]
    jsonDict = { "message" : content, "users" : users }

    auth = HTTPBasicAuth(app.config["NOTIFCATION_AUTH_USER"],
                            app.config["NOTIFICATION_AUTH_PASSWORD"]))

    requests.get(url, json=jsonDict, auth=auth)
