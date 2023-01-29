import os
from constants import *
import filesystem

def buildPath(contractLocation, flaskApp):

    base = flaskApp.config["FILESYSTEM_PROJECTS_BASE_PATH"]
    year = contractLocation.getProjectYear()
    path = os.path.join(base, "Jahr {}".format(year))
    pathWithName = os.path.join(path, contractLocation.nachname.strip())

    returnPath = None
    if os.path.isdir(pathWithName):
        returnPath = pathWithName
    else:
        returnPath = path # the year path

    return (returnPath, contractLocation.getProjectDir(), year)

def find(path, projectDir, year, app, prioKeywords, startInProjectDir=False, isFqPath=False):

    if os.path.isdir(path):
        return [ os.path.join(path, f) for f in os.listdir(path) ]
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

def filesToFileItems(files, app):
    fileItems = []
    for f in files:
        filetype = ""
        if f.lower().endswith("docx"):
            filetype = "Dokument"
        elif f.lower().endswith("jpg"):
            filetype = "Bild"
        elif f.lower().endswith("pdf"):
            filetype = "PDF"
        else:
            filetype = "unknown"

        fi = filesystem.FileItem(f, filetype, samba=True)
        fi.extraInfo = "PDF"
        fileItems.append(fi)
    return fileItems
