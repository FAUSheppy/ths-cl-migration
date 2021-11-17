import os.path
import glob
import docx

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
    raise NotImplementedError("This probs not safe yet")
    tmpDir = "tmp-{}".format(projectId)
    os.mkdir(tmpDir)
    fullTempPath = os.path.join(tmpDir, path)
    os.copy(path, fullTempPath)
    os.system("unzip {}".format(fullTempPath))
    os.system('''sed -i 's/val="55"/val="{}"/ {}"'''.format(
                    projectId, os.path.join(tmpDir, "word/settings.xml")))
    os.remove(fullTempPath)
    os.system("zip -r {target} {tmpDir}/*".format(target=fullTempPath, tmpDir=tmpDir))
    
    content = None
    with open("fullTempPath", "rb") as f:
        content = f.read()

    # xmllint --format word/settings.xml
    # replace <w:activeRecord w:val="55"/>
    # replace  <w:query w:val="SELECT * FROM C:\THS\Korrespo\THS_Auftragsorte.docx"/>
    # re-zip
    # load as bystream

    return content
