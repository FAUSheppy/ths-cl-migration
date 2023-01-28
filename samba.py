from smbprotocol.connection import Connection, Dialects
import smbprotocol.exceptions
import smbclient
import os
import stat
import datetime

from constants import *
import filesystem

import docx
import bwa

def _buildSmbPath(path, app):
    return "\\\\{}\{}\\{}".format(app.config["SMB_SERVER"], app.config["SMB_SHARE"], path)

def buildPath(cl, app):

    base = "THS_Proj"
    year = cl.getProjectYear()
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

    return (pathToReturn, cl.getProjectDir(), year)

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
        fi.extraInfo = _fsInfoFile(fi.fullpath, app)
        fileItems.append(fi)
    return fileItems

def getFile(fqSambaPath):
    with smbclient.open_file(fqSambaPath, "rb") as fd:
        return fd.read()

def carefullySaveFile(content, path):
    try:
        stat.S_ISDIR(smbclient.lstat(path).st_mode)
        return (None, WARNING_PATH_EXISTS_NO_CHANGE.format(path))
    except:
        with smbclient.open_file(path, "wb") as fd:
            fd.write(content)
        return (path, None)

def _fsInfoFile(smbfile, app):
    basename = os.path.basename(smbfile)
    if not ( ( basename.startswith("Rechnung") or basename.startswith("R-") )
            and basename.endswith(".docx") ):
        return None

    TABLE_BANKING_INFO = 0
    TABLE_INVOICE_INFO = 1

    COL_STRING_INFO = 1
    COL_CURRENCY    = 2
    COL_VALUE       = 3

    # copy file for local analysis #
    localCopyPath = os.path.join("tmp-files", os.path.basename(smbfile))
    with smbclient.open_file(smbfile, "rb") as fd:
        with open(localCopyPath, "wb") as fout:
            fout.write(fd.read())

    invoice = docx.Document(localCopyPath)
    table = invoice.tables[TABLE_INVOICE_INFO]
    
    netto  = float(table.rows[-3].cells[COL_VALUE].text.replace(",","."))
    vat    = float(table.rows[-2].cells[COL_VALUE].text.replace(",","."))
    brutto = float(table.rows[-1].cells[COL_VALUE].text.replace(",","."))

    lastPrinted = invoice.core_properties.last_printed

    # check if ever printed #
    if lastPrinted < datetime.datetime(2001, 1, 1):
        lastPrinted = None

    bwaPaidState = bwa.getPaidStateForFile(smbfile, app)
    return filesystem.ExtraInfo(lastPrinted, brutto, vat, netto, bwaPaidState)

def filesystemInfoDir(dirPath, app):

    dirPath = dirPath.replace("/","\\")
    print(dirPath)
    listing = smbclient.listdir(dirPath)
    for name in listing:
        ret = _fsInfoFile(name)
        if ret:
            return ret
    return None
