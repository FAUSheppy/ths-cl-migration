#!/usr/bin/python3

import argparse
import docx

import os
import sys
import datetime

from sqlalchemy import Column, Integer, String, Boolean, or_, and_
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func
import sqlalchemy

import ContractLocation

HEADER_CELL_ZERO = "Proj-Id"
sm = None
engine = None

def rowCellsToContractLocation(cells):
    cells = list([c.text.replace("-","") for c in cells])
    try:
        laufNrStr = cells[1].replace("JS","")
        plzStr = cells[8]
        plzNr  = None
        try:
            plzNr = int(plzStr)
        except ValueError:
            pass

        return ContractLocation.ContractLocation(
            lfn           = int(laufNrStr),
            projectid     = int(cells[0].replace("-", "") + laufNrStr),
            firma         = cells[2], 
            bereich       = cells[3], 
            geschlecht    = cells[4], 
            vorname       = cells[5], 
            nachname      = cells[6], 
            adresse_fa    = cells[7], 
            plz_fa        = plzNr,
            ort_fa        = cells[9], 
            tel_1         = cells[10],
            mobil         = cells[11], 
            fax           = cells[12], 
            auftragsort   = cells[13], 
            auftragsdatum = cells[14], 
            date_parsed   = 0
        )
    except Exception as e:
        print(e)
        return None

    raise AssertionError("WTF")

def parseTable(table):
    cells = table._cells
    for rowIndex in range(len(cells)//table._column_count):

        # skip header row #
        rowStartCell = rowIndex*table._column_count
        allCellsInLine = cells[rowStartCell:rowStartCell + table._column_count]
        if cells[rowStartCell].text == HEADER_CELL_ZERO:
            continue

        cl = rowCellsToContractLocation(allCellsInLine)
        if not cl:
            continue

        session = sm()
        print(cl.projectid)
        session.merge(cl)
        session.commit()

def dumpData(file):
    session = sm()
    allCl = session.query(ContractLocation.ContractLocation).all()
    with open(file, "a") as f:
        first = True;
        for cl in allCl:
            ad = session.query(ContractLocation.AdditionalDate).filter(ContractLocation.AdditionalDate.projectid == cl.projectid).first()
            atttributes = [a for a in dir(cl) if not a.startswith('_') and not callable(getattr(cl, a)) and not a in ["registry", "metadata"]]

            # create header on first run
            if first:
                f.write("$".join(atttributes + ["Weitere Auftragsdaten"]))
                f.write("\n")
                first = False

            strings = [ getattr(cl, a) for a in atttributes ]
            strings.append(ad)

            line = "$".join([str(s) for s in strings])
            f.write(line)
            f.write("\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse a docx with a table database')
    parser.add_argument('--db', default="sqlite:///database.sqlite",
                                    help='DB String to feed to sqlalchemy create engine')
    parser.add_argument('--dump-file', help='Dump to a file instead of reading in')
    parser.add_argument('--files', required=False, nargs='+', help='The docx-file to parse')
    args = parser.parse_args()

    engine = sqlalchemy.create_engine(args.db)
    sm = sessionmaker(bind=engine)

    if args.dump_file:
        dtString = datetime.datetime.now().strftime("%y_%d_%m_%H_%M")
        targetFile = args.dump_file + "_" + dtString + ".csv"
        if os.path.exists(targetFile):
            string = "Refusing to dump to existing file {}".format(targetFile)
            print(string, file=sys.stderr)
            sys.exit(1)
        else:
            dumpData(targetFile)
            with open(".backup_info", "w") as f:
                f.write(dtString)
            sys.exit(0)

    if not args.files:
        print("No files to read in.", file=sys.stderr)
        sys.exit(1)

    for f in args.files:
        if args.dump_file:
            print("ERROR: --dump-file was specified, refusing to edit database", file=sys.stderr)
            sys.exit(1)
        document = docx.Document(f)
        ContractLocation.getBase().metadata.create_all(engine)

        for table in document.tables:
            parseTable(table)
