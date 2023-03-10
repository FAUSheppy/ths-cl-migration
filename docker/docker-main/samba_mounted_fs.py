import os
import flask
from constants import *
import glob
import filesystem

def buildPath(contractLocation):

    base = flask.current_app.config["FILESYSTEM_PROJECTS_BASE_PATH"]
    year = contractLocation.getProjectYear()
    path = os.path.join(base, "Jahr {}".format(year))
    pathWithName = os.path.join(path, contractLocation.nachname.strip())

    returnPath = None
    if os.path.isdir(pathWithName):
        returnPath = pathWithName
    else:
        returnPath = path # the year path

    return (returnPath, contractLocation.getProjectDir(), year)

def find(projectDir, year):

    # FIXME use prio keywords
    if not year or not projectDir:
         raise ValueError("Missing Input parameter (year={}, dir={})".foramt(year, projectDir))
 
    base = flask.current_app.config["FILESYSTEM_PROJECTS_BASE_PATH"]
    searchString = "./Jahr {}/**/{}".format(year, projectDir)
    fullSearchPath = os.path.join(base, searchString)
    print("Search for: '{}'".format(fullSearchPath))
    result = list(glob.glob(fullSearchPath, recursive=True))
    if len(result) == 0:
        print("Project dir not found")
        return None
    else:
        print("Search results: ", result)
        return result[0] # FIXME, stop after finding firstpath??

def listFiles(path):
    if os.path.isdir(path):
        return [ os.path.join(path, f) for f in os.listdir(path) ]
    else:
        raise ValueError("Path does not exist or not a valid path: '{}'".format(path))

def carefullySaveFile(content, path):

    # fix path if nessesary
    if path.startswith(flask.current_app.config["CLIENT_PATH_PREFIX"]):
        path = path.replace(flask.current_app.config["CLIENT_PATH_PREFIX"], "")

    if not path.startswith(flask.current_app.config["FILESYSTEM_PROJECTS_BASE_PATH"]):
        path = os.path.join(flask.current_app.config["FILESYSTEM_PROJECTS_BASE_PATH"], path)

    # check path exists #
    if os.path.exists(path):
        return (None, WARNING_PATH_EXISTS_NO_CHANGE.format(path))
    else:
        with open(path, 'wb') as f:
            f.write(content)
        return (path, None)

def getFile(path):
    with open(path) as f:
        return f.read()

def deleteClient():
    # not needed #
    pass

def createClient():
    # not needed #
    pass
