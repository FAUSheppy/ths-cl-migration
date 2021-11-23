from smbprotocol.connection import Connection, Dialects
import smbprotocol.exceptions
import smbclient
import os
import stat
import datetime

from constants import *
import filesystem

def _buildSmbPath(path, app):
    return "\\\\{}\{}\\{}".format(app.config["SMB_SERVER"], app.config["SMB_SHARE"], path)

def buildPath(cl, app):

    base = "THS_Proj"
    nrStr = str(cl.projectid)
    
    try:
        year = datetime.datetime.strptime(cl.auftragsdatum, DB_DATE_FORMAT).year
    except ValueError:
        year = 2000 + int(nrStr[-7:-5])
        print("Failed to parse date correctly, assuming {} form projectId".format(year))
        if year < 2008:
            try:
                year = int(cl.auftragsdatum.split(".")[-1])
                print("Too early, trying to strip from maleformed date anyway, got {}".format(year))
            except ValueError as e:
                print("Unparsable, cannot determine path: {}".format(e))
                return ("", "", "")

    path = base + "\Jahr " + str(year) 
    pathWithName = path + "\\" + cl.nachname.strip() 

    # see if the more specific path (with name) exists #
    pathToReturn = None
    try:
        check = _buildSmbPath(pathWithName, app)
        smbclient.lstat(check)
        pathToReturn = pathWithName
    except smbprotocol.exceptions.SMBOSError:
        print("Specific path {} doesn't seem to exist, using year-path".format(pathWithName))
        pathToReturn = path

    # build p-dir based on format of the give year # 
    if year < 2020:
        endIdent = nrStr[-5:]
        yearIdent = nrStr[-7:-5]
        monthIdent = nrStr[:-7]
        if len(monthIdent) == 1:
            monthIdent = "0" + monthIdent
        projectDir  = "P-{month}-{year}-{end}".format(month=monthIdent, year=yearIdent, 
                                                            end=endIdent)
    else:
        lfn = nrStr[-4:]
        dt  = nrStr[:-4]
        assert len(dt) >= 3
        if len(dt) == 3:
            dt = "0" + dt
        projectDir  = "P-{}-{}".format(dt, lfn)


    
    print(pathToReturn, projectDir, year, cl.nachname)
    return (pathToReturn, projectDir, year)

def _recursiveFind(base, projectDirToLookFor, inProjectDir, prioKeywords, isHighPrioPath):

    files = []
    isDir = stat.S_ISDIR(smbclient.lstat(base).st_mode)
    if not isDir and inProjectDir:
        return [base]
    elif not isDir:
        return []
    else:

        # get current listing #
        listing = smbclient.listdir(base)

        # define high and low prio list #
        highPrioLambda = lambda x: any( [w in x.lower() for w in prioKeywords]) or inProjectDir

        lowPrioLambda = lambda x: not highPrioLambda(x)
        highPrio = filter(highPrioLambda, listing)
        lowPrio = filter(lowPrioLambda, listing)

        # search high prio first, then low prio #
        for subPath in highPrio:
            files += _recursiveFind(base + "/" + subPath, projectDirToLookFor,
                                        inProjectDir or projectDirToLookFor == subPath,
                                        prioKeywords, True)
        if files:
            return files
        elif isHighPrioPath:
            for subPath in lowPrio:
                files += _recursiveFind(base + "/" + subPath, projectDirToLookFor,
                                        inProjectDir or projectDirToLookFor == subPath,
                                        prioKeywords, isHighPrioPath)
            return files
        else:
            return []

def find(path, projectDir, year, app, prioKeywords, startInProjectDir=False, isFqPath=False):
    base = path
    if not isFqPath:
        base = _buildSmbPath(path, app)
    try:
        files = _recursiveFind(base, projectDir, startInProjectDir,
                                prioKeywords, False or isFqPath)
    except smbprotocol.exceptions.SMBOSError as e:
        print("Find {} failed {}".format(base, e))
        return []
    return files

def initClient(server, user, password, app):
    app.config["SMB_SESSION"] = smbclient.register_session(server, username=user, password=password)

def deleteClient(app):
    app.config["SMB_SESSION"] = smbclient.delete_session(app.config["SMB_SERVER"])

def filesToFileItems(files):
    fileItems = []
    for f in files:
        fileItems.append(filesystem.FileItem(f, "netzwerk", samba=True))
    return fileItems

def getFile(fqSambaPath):
    with smbclient.open_file(fqSambaPath, "rb") as fd:
        return fd.read()

def carefullySaveFile(content, path):
    try:
        stat.S_ISDIR(smbclient.lstat(path).st_mode)
        return (None, '''Eine Datei oder ein Ordner mit diesem Name existiert bereits.<br>
                Es wurden keine Änderungen vorgenommen.<br>
                Pfad: {}'''.format(path))
    except:
        with smbclient.open_file(path, "wb") as fd:
            fd.write(content)
        return (path, None)
