import os
from constants import *

def buildPath(contractLocation, flaskApp):

    base = flaskApp.config["FILESYSTEM_RPOEJECTS_BASE_PATH"]
    year = contractLocation.getProjectYear()
    path = os.path.join(base, "Jahr {}".format(year))
    pathWithName = os.path.join(path, contractLocation.nachname.strip())

    returnPath = None
    if os.path.isdir(pathWithName):
        returnPath = pathWithName
    else:
        returnPath = path # the year path

    return (pathToReturn, cl.getProjectDir(), year)

def find(path, projectDir, year, app, prioKeywords, startInProjectDir=False, isFqPath=False):

    if os.path.isdir(path):
        return os.listdir(os.path)
    else:
        return []

def carefullySaveFile(content, path):
    if os.path.exists(path):
        return (None, WARNING_PATH_EXISTS_NO_CHANGE.format(path))
    else:
        with open(path, 'w') as f:
            f.write(content)

def getFile(path):
    with open(path) as f:
        return f.read()

def deleteClient():
    # not needed #
    pass

def createClient():
    # not needed #
    pass
