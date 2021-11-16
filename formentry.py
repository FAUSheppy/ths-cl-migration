from constants import *

def formEntryArrayFromColNames(colNames):
    formEntries = []
    for i in range(0, len(colKeys)):
        formEntries += FormEntry(colNames[i])
    return formEntries

class FormEntry:
    def __init__(self, colName, typeAsText):
        self.colName     = colName
        self.displayName = getDisplayNameSafe(colName)
        self.typeAsText  = getColTypeSafe(colName)
        self.options     = getOptionsSafe(colName)

    def getDisplayNameSafe(colName):
        if colName in COLS_TO_DISPLAY_NAME:
            return COLS_TO_DISPLAY_NAME[colName]
        else:
            return colName

    def getColTypeSafe(colName):
        typeAsText = "text"
        if colKeys[i] in IS_INT_TYPE:
            typeAsText  = "number"
        if colKeys[i] in IS_DATE_TYPE:
            typeAsText  = "date"
        if colKeys[i] in IS_TEL_TYPE:
            typeAsText  = "tel"
        return typeAsText

    def getOptionsSafe(colName):
        if colName in COL_NAMES_TO_OPTIONS:
            return COL_NAMES_TO_OPTIONS[colName]
        else:
            return None
