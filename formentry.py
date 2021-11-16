from constants import *

def formEntryArrayFromColNames(colNames, contractLocation):
    formEntries = []
    for i in range(0, len(colNames)):
        formEntries.append(FormEntry(colNames[i], contractLocation))
    return formEntries

class FormEntry:

    def __init__(self, colName, contractLocation=None):
        self.colName = colName
        self.value = ""
        if contractLocation:
            self.value = getattr(contractLocation, colName)

        self.displayName = FormEntry.getDisplayNameSafe(colName)
        self.typeAsText  = FormEntry.getColTypeSafe(colName)
        self.options     = FormEntry.getOptionsSafe(colName)

    def getDisplayNameSafe(colName):
        if colName in COLS_TO_DISPLAY_NAME:
            return COLS_TO_DISPLAY_NAME[colName]
        else:
            return colName

    def getColTypeSafe(colName):
        typeAsText = "text"
        if colName in IS_INT_TYPE:
            typeAsText  = "number"
        if colName in IS_DATE_TYPE:
            typeAsText  = "date"
        if colName in IS_TEL_TYPE:
            typeAsText  = "tel"
        return typeAsText

    def getOptionsSafe(colName):
        if colName in COL_NAMES_TO_OPTIONS:
            return COL_NAMES_TO_OPTIONS[colName]
        else:
            return None
