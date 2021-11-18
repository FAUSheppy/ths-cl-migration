from smbprotocol.connection import Connection, Dialects
import smbclient
import os
import stat
import datetime

from constants import *
import filesystem

def buildPath(cl):

    base = "THS_Proj"
    nrStr = str(cl.projectId)
    
    try:
        year = datetime.datetime.strptime(cl.auftragsdatum, DB_DATE_FORMAT).year
    except ValueError:
        year = 2000 + int(nrStr[-7:-5])
        print("Failed to parse date correctly, assuming {} form projectId".format(year))

    path = base + "\Jahr " + str(year) + "\\" + cl.nachname.strip()

    endIdent = nrStr[-5:]
    yearIdent = nrStr[-7:-5]
    monthIdent = nrStr[:-7]

    if len(monthIdent) == 1:
        monthIdent = "0" + monthIdent

    projectDir  = "P-{month}-{year}-{end}".format(month=monthIdent, year=yearIdent, end=endIdent)
    
    print(path, projectDir, year, cl.nachname)
    return (path, projectDir, year)

def _recursiveFind(base, projectDirToLookFor, inProjectDir):

    files = []
    isDir = stat.S_ISDIR(smbclient.lstat(base).st_mode)
    if not isDir and inProjectDir:
        return [base]
    elif not isDir:
        return []
    else:
        listing = smbclient.listdir(base)
        for subPath in listing:
            files += _recursiveFind(base + "/" + subPath,
                                projectDirToLookFor,
                                inProjectDir or projectDirToLookFor == subPath)

        return files

def find(path, projectDir, year, app):
    base = "\\\\{}\{}\\{}".format(app.config["SMB_SERVER"], app.config["SMB_SHARE"], path)
    files = _recursiveFind(base, projectDir, False)
    print(files)
    return files

def initClient(server, user, password, app):
    app.config["SMB_SESSION"] = smbclient.register_session(server, username=user, password=password)
    print(app.config["SMB_SESSION"])

def filesToFileItems(files):
    fileItems = []
    for f in files:
        fileItems.append(filesystem.FileItem(f, "netzwerk", samba=True))
    return fileItems
