import os
import os.path
import subprocess
import glob
import json
import shutil
import werkzeug
import zipfile

class ExtraInfo:

    def __init__(self, lastPrinted, brutto, vat, netto, alreadyPaid=False):

        self.lastPrinted = lastPrinted
        self.brutto = brutto
        self.vat = vat
        self.netto = netto
        self.alreadyPaid = alreadyPaid

class FileItem:

    def __init__(self, fullpath, fileType, samba=False):
        self.fullpath = fullpath
        self.name = os.path.basename(fullpath)
        self.fileType = fileType
        self.deletetable = not samba
        self.localpath = ""
        self.extraInfo = None

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

def getTemplates(path=""):
    if path:
        retDict = dict()
        basepath = os.path.join("./document-templates/", path)
        for fname in os.listdir(basepath):
            if fname.endswith(".docx"):
                fullpath = os.path.join(basepath, fname)
                retDict.update({ fname : { "description" : "", "year" : 0 }})
        return retDict
    with open("./document-templates/templates.json", encoding="utf-8") as f:
        return json.loads(f.read())

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
    fileContentTmp = fileContentTmp.replace('''SELECT * FROM &quot;ths_word_helper&quot;''',
        '''SELECT * FROM &quot;ths_word_helper&quot; WHERE &quot;projectid&quot; = {}'''.format(projectId))
    fileContentTmp = fileContentTmp.replace("localhost", app.config["DB_SERVER"])
    
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
