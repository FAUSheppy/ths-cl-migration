import requests
from constants import *
from requests.auth import HTTPBasicAuth

def makeRepresentation(oldCl, oldAd, cl, ad):
    dates = ad.dates

    contentString = ""

    if not oldCl:
        startString = "Neuer Eintrag: {}\n".format(cl.projectId)
    else:
        startString = "Änderung von Eintrag: {}\n".format(oldCl.projectId)

    for key in cl.toDict():
        
        # new entry #
        new = getattr(cl, key)
        if not oldCl:
            contentString += "{}: {}\n".format(key, new)
            continue

        # changing old entry #
        old = getattr(oldCl, key)
        if new != old:
            contentString += "{}: {} -> {}\n".format(COLS_TO_DISPLAY_NAME[key], old, new)
            continue
    
    if not oldAd and ad.dates:
        contentString += "\n" + ad.dates

    return startString +  contentString

def sendSignal(content, app):

    url      = app.config["NOTIFICATION_URL"]
    users    = app.config["NOTIFICATION_USERS"]
    jsonDict = { "message" : content, "users" : users }

    print(content)

    auth = HTTPBasicAuth(app.config["NOTIFICATION_AUTH_USER"], app.config["NOTIFICATION_AUTH_PASS"])

    requests.post(url, json=jsonDict, auth=auth)
