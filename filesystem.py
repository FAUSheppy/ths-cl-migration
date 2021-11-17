import os.path
import subprocess
import glob
import docx
import shutil

class FileItem:

    def __init__(self, fullpath, fileType):
        self.fullpath = fullpath
        self.name = os.path.basename(fullpath)
        self.fileType = fileType

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
    filenameList = glob.glob("./document-templates/*.docx")
    templateList = []
    for f in filenameList:
        templateList.append(DocumentTemplate(f))
    print(templateList)
    return templateList

def getDocumentInstanceFromTemplate(path, projectId):
    # unzip docx
    #raise NotImplementedError("This probs not safe yet")

    tmpDir = "tmp-{}".format(projectId)
    try:
        os.mkdir(tmpDir)
    except FileExistsError:
        pass

    fullTempPath = os.path.join(tmpDir, os.path.basename(path))
    shutil.copy2(path, fullTempPath)

    # unpack docx-d is outdir and -o is overwrite
    print("unzip -o {} -d {}".format(fullTempPath, tmpDir))
    os.system("unzip -o {} -d {}".format(fullTempPath, tmpDir))

    # edit xml
    print('''sed -i 's/val="55"/val="{}"/' {}'''.format(
                    projectId, os.path.join(tmpDir, "word/settings.xml")))
    os.system('''sed -i 's/val="55"/val="{}"/' {}'''.format(
                    projectId, os.path.join(tmpDir, "word/settings.xml")))

    # remove old file
    print(fullTempPath)
    os.remove(fullTempPath)

    # repack into new docx
    p = subprocess.Popen(["/usr/bin/zip","-r", os.path.basename(fullTempPath), "."], cwd=tmpDir)
    p.communicate()
   
    # transform new file into bitstream
    content = None
    with open(fullTempPath, "rb") as f:
        content = f.read()

    # remove new file
    # os.remove(fullTempPath)

    return content
