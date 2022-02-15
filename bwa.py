import xlrd

BWA_COL_LFN = 1

COLOR_ID_TO_STATE_ID = {
    64 : 0,
    13 : 5,
    40 : 10
}

COLOR_ID_TO_COLOR_NAME = {
    64 : "white",
    13 : "yellow",
    40 : "aliceblue"
}

STATE_NAMES = {
    0 : "no_invoice",
    5 : "unpaid_invoice",
    10 : "paid_invoice"
}

def datetimeFromXls(xlsDateAsFloat):
    if not xlsDateAsFloat or not type(xlsDateAsFloat) == float:
        return None
    return xlrd.xldate_as_datetime(xlsDateAsFloat, 0)

class BWAEntry:
    def __init__(self, row, color):

        self.color = color
        self.rawRow = row

        self.lfn          = int(row[1].value)
        self.auftraggeber = row[2].value
        self.typeRaw      = row[3].value
        self.dateRaw      = row[4].value
        self.netto        = row[5].value
        self.brutto       = row[6].value
        self.dueDateRaw   = row[7].value
        self.paidDateRaw  = row[8].value
        self.unusedLfn    = row[9].value
        self.mahnungRaw   = row[10].value
        
        # derived values
        self.pid      = row[0].value + str(self.lfn).zfill(4)
        self.state    = COLOR_ID_TO_STATE_ID[self.color]
        self.date     = datetimeFromXls(self.dateRaw)
        self.dueDate  = datetimeFromXls(self.dueDateRaw)
        self.paidDate = datetimeFromXls(self.paidDateRaw)

    def stateToString(self):
        return STATE_NAMES[self.state]

    def colorToString(self):
        return COLOR_ID_TO_COLOR_NAME[self.color]

    def equalsDbEntry(self, dbEntry):
        
        return None

    def __repr__(self):
        return "{pid} by {source} of type {tt} on {date}".format(
                        pid=self.pid, source=self.auftraggeber, tt=self.typeRaw, date=self.date)

def _getLineNrFromLfn(wbSheet, lfn, mustExist=True):

    getHeaderRow = wbSheet.row(0)
    firstRowLfn = int(firstSheet.row(1)[BWA_COL_LFN].value)

    # naive assumption first
    targetRow = getRowByLfn - firstRowLfn + 1

    if not mustExist:
        return targetRow
        
    # check & fallback
    while (targetRow > 0 and
            targetRow < firstSheet.nrows):
    
        print("Target Row:", targetRow)

        row = firstSheet.row(targetRow)
        foundLfn = None
        try:
            foundLfn = int(row[BWA_COL_LFN].value)
        except ValueError:
            return None

        if foundLfn == getRowByLfn:
            return targetRow
        elif foundLfn > getRowByLfn:
            targetRow -= 1
        else:
            targetRow +=1

        print("Warning unexpected LFN ({}) in row {}".format(foundLfn, targetRow))

    return None


def saveClToBwa(filename, cl, owerwrite=False):

    wb = xlrd.open_workbook(filename, formatting_info=True)
    firstSheet = wb.sheets()[0]
    targetRow = _getLineNrFromLfn(getRowByLfn, mustExist=False) 
    row = firstSheet.rows()[targetRow]

    for i in range(1, 11):
        if row[i].value == "":
            row[i].value == cl.getBwaCol(i)

    wb.save()
    finally:
        wb.close()



def getBwaEntryForLfn(filename, getRowByLfn):

    wb = xlrd.open_workbook(filename, formatting_info=True)
    firstSheet = wb.sheets()[0]
    targetRow = _getLineNrFromLfn(getRowByLfn, mustExist=True) 

    if not targetRow:
        return None
    else:
        color = getColorOfRow(firstSheet, wb, targetRow)
        row = firstSheet.rows()[targetRow]
        return BWAEntry(row, color)

    finally:
        wb.close()

def getColorOfRow(sheet, wb, row):
    cellXfIndex = sheet.cell_xf_index(row, 0)
    styleEntry = wb.xf_list[cellXfIndex]
    bgc = styleEntry.background.pattern_colour_index
    return bgc
    
def checkFileLocked(filename):
    return False # TODO

def getPaidStateForFile(smbfile, app):
    tmp = smbfile.split(".docx")[0].split("-")
    lfn = int(tmp[-1])
    pidShort = tmp[-2]
    entry = getBwaEntryForLfn(app.config["BWA_FILE"], lfn)
    return entry and entry.state == 10
