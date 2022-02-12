import xlrd

BWA_COL_LFN = 1

def getLFnInBwa(filename, app, getRowByLfn):
    wb = xlrd.open_workbook(filename, formatting_info=True)
    firstSheet = wb.sheets()[0]
    
    getHeaderRow = firstSheet.row(0)
    firstRowLfn = firstSheet.row(1)[BWA_COL_LFN]

    # naive assumption first
    targetRow = getRowByLfn-firstRowLfn + 1
        
    # check & fallback
    while targetRow > 0 and
            targetRow < firstSheet.nrows:
            
        row = firstSheet.row(targetRow)
        foundLfn = row[BWA_COL_LFN]
        if foundLfn == getRowByLfn:
            color = getColorOfRow(firstSheet, wb, targetRow)
            return (row, color)
        elif foundLfn > getRowByLfn:
            targetRow -= 1
        else:
            targetRow +=1
        print("Warning unexpected LFN ({}) in row {}".format(
                        foundLfn, targetRow))
                        
    return (None, None)
        
def getColorOfRow(sheet, wb, row):
    cellXfIndex = sheet.cell_xf_index(row, 0)
    return None
    