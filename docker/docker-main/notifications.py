import requests
from constants import *
from requests.auth import HTTPBasicAuth

def makeRepresentation(oldCl, oldAd, cl, ad):
    dates = ad.dates

    contentString = ""

    if not oldCl:
        startString = "Neuer Eintrag: {}\n".format(cl.projectid)
    else:
        startString = "Änderung von Eintrag: {}\n".format(oldCl.projectid)

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

def sendError(e, errorLines, app):

    url      = app.config["LOG_SERVER"]
    jsonDict = { "service" : app.config["LOG_SERVICE"],
                 "host"    : app.config["LOG_HOST"],
                 "contentType" : "MULTILINE",
                 "severity"    : 1,
                 "content"     : errorLines }

    auth = HTTPBasicAuth(app.config["LOG_AUTH_USER"], app.config["LOG_AUTH_PASS"])
    r = requests.put(url, json=jsonDict, auth=auth)
    # print(r.text)
