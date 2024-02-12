import os
import os.path
import subprocess
import glob
import json
import shutil
import werkzeug
import zipfile
import flask
import urllib.parse
import analyser

def addBasePath(path):
    serverPathPrefix = flask.current_app.config["FILESYSTEM_PROJECTS_BASE_PATH"]
    if path.startswith(serverPathPrefix):
        return path
    else:
        return os.path.join(serverPathPrefix, path.rstrip("/"))

def removeBasePath(path):
    serverPathPrefix = flask.current_app.config["FILESYSTEM_PROJECTS_BASE_PATH"]
    if path.startswith(serverPathPrefix):
        return path[len(serverPathPrefix):]
    else:
        return path

class FileItem:

    def __init__(self, fullpath):

        self.fullpath = fullpath
        self.serverRelativePath = removeBasePath(fullpath)
        self.downloadUrl = urllib.parse.quote_plus(self.serverRelativePath)
        self.name = os.path.basename(fullpath)
        self.fileType = self._getFileType()
        self.deletetable = False
        self.remoteAccessPath = self._getRemoteAccessPath()
        self.extraInfo = self._getExtraInfo()

    def __lt__(self, other):
        
        ORDERING = [ "Dokument (Rechnung)", "PDF (Rechnung)", "Dokument", "Bild", "unknown"]
        valueSelf  = ORDERING.index(self.fileType)
        valueOther = ORDERING.index(other.fileType)

        if valueSelf == -1:
            return True
        if valueOther == -1:
            return False
        return valueSelf < valueOther

    def _getRemoteAccessPath(self):
        
        clientPathPrefix = flask.current_app.config["CLIENT_PATH_PREFIX"]

        path = clientPathPrefix + removeBasePath(self.fullpath)
        windowsPath = path.replace("/", "\\")
        return windowsPath

    def _getFileType(self):

        filetype = ""
        fname = self.name.lower()
        if "~$" in fname: # docx lockfile (keep first)
            return "unknown"
        elif fname.endswith("docx") or fname.endswith("doc"):
            if "Rechnung" in self.name or "R-" in self.name:
                filetype = "Dokument (Rechnung)"
            else:
                filetype = "Dokument"
        elif fname.endswith("jpg"):
            filetype = "Bild"
        elif fname.endswith("png"):
            filetype = "Bild"
        elif fname.endswith("pdf"):
            if "Rechnung" in self.name or "R-" in self.name:
                filetype = "PDF (Rechnung)"
            else:
                filetype = "Dokument"
        else:
            filetype = "unknown"

        return filetype

    def _getExtraInfo(self):
        return analyser.analyseDocument(self)

def itemsArrayFromDbEntries(dbEntries):
    if not dbEntries:
        return []
    
    fileListItems = []
    for entry in dbEntries:
        fileListItems.append(FileItem(entry.fullpath, entry.fileType))

    return fileListItems

class DocumentTemplate:
    def __init__(self, fullpath):
        self.fullpath = fullpath
        self.name = os.path.basename(fullpath)

def getTemplates(path="."):

    retDict = dict()
    basepath = os.path.join("./document-templates/", path)

    if not os.path.isdir(basepath):
        return dict()

    for fname in os.listdir(basepath):
        if fname.endswith(".docx"):
            fullpath = os.path.join(basepath, fname)
            retDict.update({ fname : { "description" : "", "year" : 0 }})

    return retDict

def getDocumentInstanceFromTemplate(path, projectId, lfn, app):
    print(path)
    # just be save here #
    projectId = str(int(projectId))

    tmpDir = "tmp-{}".format(projectId)

    # remove old working dir #
    if os.path.isdir(tmpDir):
        shutil.rmtree(tmpDir)

    # recreate dir
    os.mkdir(tmpDir)

    fullTempPath = os.path.join(tmpDir, os.path.basename(path))
    shutil.copy2(path, fullTempPath)

    # unpack docx-d is outdir and -o is overwrite
    with zipfile.ZipFile(fullTempPath, 'r') as zf:
        zf.extractall(tmpDir)

    # edit xml (add active record + query) #
    xmlPath = os.path.join(tmpDir, "word/settings.xml")
    
    fileContentTmp = None
    with open(xmlPath, 'r') as f:
        fileContentTmp = f.read()

    
    with open("debug_pre.xml", "w") as f:
        f.write(fileContentTmp)

    # TODO make this configurable
    fileContentTmp = fileContentTmp.replace('''<w:mailMerge>''',
        '''<w:mailMerge><w:viewMergedData/><w:activeRecord w:val="1"/>''')

    # delete project ID zero if its in the file #
    fileContentTmp = fileContentTmp.replace(" WHERE &quot;projectid&quot; = 0", "")
    fileContentTmp = fileContentTmp.replace(" WHERE &quot;projectid&quot; = '0'", "")

    # input the correct project id #
    fileContentTmp = fileContentTmp.replace('''SELECT * FROM &quot;ths_word_helper&quot;''',
        '''SELECT * FROM &quot;ths_word_helper&quot; WHERE &quot;projectid&quot; = {}'''.format(projectId))

    # fix old IPs that may still hide in the file #
    fileContentTmp = fileContentTmp.replace("localhost", app.config["DB_SERVER"]) #TODO dafug?
    fileContentTmp = fileContentTmp.replace("192.168.178.67", app.config["DB_SERVER"])
    fileContentTmp = fileContentTmp.replace("5432", str(app.config["PG_OUTSIDE_PORT"]))
    
    with open("debug_post.xml", "w") as f:
        f.write(fileContentTmp)


    with open(xmlPath, 'w') as f:
        f.write(fileContentTmp)

    # remove old result file
    os.remove(fullTempPath)

    # repack into new docx
    shutil.make_archive("../" + fullTempPath, 'zip', root_dir=tmpDir, base_dir=".")
    os.rename("../" + fullTempPath + ".zip", fullTempPath)
   
    # transform new file into bitstream
    content = None
    with open(fullTempPath, "rb") as f:
        content = f.read()

    shutil.rmtree(tmpDir)

    return content
