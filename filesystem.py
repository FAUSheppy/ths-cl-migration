import os.path
import subprocess
import glob
import json
import shutil
import werkzeug

class FileItem:

    def __init__(self, fullpath, fileType, samba=False):
        self.fullpath = fullpath
        self.name = os.path.basename(fullpath)
        self.fileType = fileType
        self.deletetable = not samba

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

def getTemplates():
    #filenameList = glob.glob("./document-templates/*.docx")
    #templateList = []
    #for f in filenameList:
    #    templateList.append(DocumentTemplate(f))
    #print(templateList)
    with open("./document-templates/templates.json", "r") as f:
        return json.loads(f.read())

def getDocumentInstanceFromTemplate(path, projectId, lfn, app):

    # just be save here #
    projectId = str(int(projectId))

    tmpDir = "tmp-{}".format(projectId)

    # remove old working dir #
    os.system("rm -rf {}".format(tmpDir))

    # recreate dir
    os.mkdir(tmpDir)

    fullTempPath = os.path.join(tmpDir, os.path.basename(path))
    shutil.copy2(path, fullTempPath)

    # unpack docx-d is outdir and -o is overwrite
    os.system("unzip -o {} -d {}".format(fullTempPath, tmpDir))

    # edit xml (lfn + query) #
    xmlPath = os.path.join(tmpDir, "word/settings.xml")
    os.system('''sed -i 's/val="55"/val="{}"/' {}'''.format(0, xmlPath))

    oldQueryString = "SELECT \* FROM &quot;contract_locations&quot;"
    newQueryString = "SELECT \* FROM \&quot;contract_locations\&quot; WHERE projectid = {}"
    newQueryStringFormated = newQueryString.format(projectId)

    sedReplaceQuery = '''sed -i 's/val="{}"/val="{}"/' {}'''
    sedReplaceQueryFmt = sedReplaceQuery.format(oldQueryString, newQueryStringFormated, xmlPath)
    print(sedReplaceQueryFmt)
    os.system(sedReplaceQueryFmt)

    # remove old result file
    os.remove(fullTempPath)

    # repack into new docx
    p = subprocess.Popen(["/usr/bin/zip", "-r", os.path.basename(fullTempPath), "."], cwd=tmpDir)
    p.communicate()
   
    # transform new file into bitstream
    content = None
    with open(fullTempPath, "rb") as f:
        content = f.read()

    return content
