import os.path
import subprocess
import glob
import json
import shutil
import werkzeug
import zipfile

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

    fileContentTmp = fileContentTmp.replace('''<w:mailMerge>''',
        '''<w:mailMerge><w:viewMergedData/><w:activeRecord w:val="1"/>''')
    fileContentTmp = fileContentTmp.replace('''SELECT * FROM &quot;contract_locations&quot;''',
        '''SELECT * FROM &quot;contract_locations&quot; WHERE &quot;projectid&quot; = {}'''.format(projectId))
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
