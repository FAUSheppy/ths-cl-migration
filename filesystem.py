import os.path

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
        fileListItems.append(FileItem(dbEntries.fullpath, dbEntries.fileType))

    return fileListItems

