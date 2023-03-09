import xlrd
import xlutils.copy
import os
import flask
#from server import ProjectPath, ContractLocation
import server

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

        if not dbEntry:
            return None

        diff = dict()
        for col in range(0, 11):
            #dbValue = dbEntry.rawRow[col]
            dbValue = None
            bwaValue = self.rawRow[col].value
            if dbValue and dbValue != bwaValue:
                diff.update( { col : (bwaValue, dbValue) } )
        return diff

    def __repr__(self):
        return "{pid} by {source} of type {tt} on {date}".format(
                        pid=self.pid, source=self.auftraggeber, tt=self.typeRaw, date=self.date)

def _getLineNrFromLfn(wbSheet, lfn, mustExist=True):

    getHeaderRow = wbSheet.row(1)
    firstRowLfn = int(wbSheet.row(2)[BWA_COL_LFN].value)

    # naive assumption first
    targetRow = lfn - firstRowLfn + 2

    if not mustExist:
        return targetRow
        
    # check & fallback
    while (targetRow > 0 and
            targetRow < wbSheet.nrows):
    
        print("Target Row:", targetRow)

        row = wbSheet.row(targetRow)
        foundLfn = None
        try:
            foundLfn = int(row[BWA_COL_LFN].value)
        except ValueError:
            return None

        if foundLfn == lfn:
            return targetRow
        elif foundLfn > lfn:
            targetRow -= 1
        else:
            targetRow +=1

        print("Warning unexpected LFN ({}) in row {}".format(foundLfn, targetRow))

    return None


def saveClToBwa(filename, cl, overwrite=False):

    rb = xlrd.open_workbook(filename, formatting_info=True)
    wb = xlutils.copy.copy(rb)
    firstSheet = rb.sheets()[0]
    targetRow = _getLineNrFromLfn(firstSheet, cl.lfn, mustExist=False)
    row = firstSheet.row(targetRow)

    for i in range(0, 11):
        clValue = cl.getBwaCol(i)
        if (row[i+1].value == "" or overwrite) and clValue:
            print("Writing to {}-{}: {}".format(targetRow, i, clValue))
            wb.get_sheet(0).write(targetRow, i, clValue)

    wb.save(filename)


def getBwaEntryForLfn(filename, getRowByLfn):

    with  xlrd.open_workbook(filename, formatting_info=True) as wb:
        firstSheet = wb.sheets()[0]
        targetRow = _getLineNrFromLfn(firstSheet, getRowByLfn, mustExist=True) 

        if not targetRow:
            return None
        else:
            color = getColorOfRow(firstSheet, wb, targetRow)
            row = firstSheet.row(targetRow)
            return BWAEntry(row, color)

def getColorOfRow(sheet, wb, row):
    cellXfIndex = sheet.cell_xf_index(row, 0)
    styleEntry = wb.xf_list[cellXfIndex]
    bgc = styleEntry.background.pattern_colour_index
    return bgc
    
def checkFileLocked(filename):
    dirname = os.path.dirname(filename)
    if dirname == "":
        dirname = "."
    return any([ "lock" in x for x in os.listdir(dirname)])


def getPaidStateForFile(name):
    tmp = name.split(".docx")[0].split("-")
    lfn = int(tmp[-1])
    pidShort = tmp[-2]
    entry = getBwaEntryForLfn(flask.current_app.config["BWA_FILE"], lfn)
    print(lfn)
    print(entry.rawRow)
    print("paid date:", entry.paidDateRaw, entry.dueDateRaw, entry.state, entry.netto)
    return entry and ( entry.state == 10 or len(entry.paidDateRaw) > 0 )

def bwa():
    db = flask.current_app.config["DB"]
    if flask.request.method == "POST": 
        projectId = flask.request.json["projectid"] 
        cl = db.session.query(ContractLocation).filter( 
                                ContractLocation.projectid == projectId).first() 
        
        if checkFileLocked(flask.current_app.config["BWA_FILE"]):
            return ("BWA File locked, refusing modification, close the file on all computers", 423)

        saveClToBwa(flask.current_app.config["BWA_FILE"], cl, 
                        overwrite=flask.request.json["overwrite"]) 
        return ("", 204) 
    else: 
        projectId = flask.request.args.get("projectid") 
        container = bool(flask.request.args.get("container")) 
       
        lfn = int(projectId[4:]) 
        
        if not projectId.startswith("23") or lfn < 977: 
            return ("BWA Entries before P-2201-0977 are not supported", 401) 

        bwaEntry = getBwaEntryForLfn(flask.current_app.config["BWA_FILE"], lfn)
        dbEntry  = db.session.query(ContractLocation).filter(
                        ContractLocation.projectid == projectId).first()

        # check if a project path is availiable #
        pp = db.session.query(ProjectPath).filter(ProjectPath.projectid == projectId).first()
        projectPathAvailiable = False
        if pp and flask.current_app.config["SAMBA"]:
            projectPathAvailiable = bool(pp.projectpath)

        filesystemInfo = None
        if projectPathAvailiable:
            filesystemInfo = fsbackend.filesystemInfoDir(pp.projectpath, flask.current_app)

        if bwaEntry:
            diff = bwaEntry.equalsDbEntry(dbEntry)
        else:
            diff = None

        if container:
            return flask.render_template("bwa_container_info.html", bwaEntry=bwaEntry,
                                            dbEntry=dbEntry, filesystemInfo=filesystemInfo)

        return flask.render_template("bwa.html", dbEntry=dbEntry, bwaEntry=bwaEntry, diff=diff)
