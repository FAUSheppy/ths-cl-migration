#!/usr/bin/python3

import argparse
import docx

from sqlalchemy import Column, Integer, String, Boolean, or_, and_
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func
import sqlalchemy

import ContractLocation

HEADER_CELL_ZERO = "Proj-Id"
engine = sqlalchemy.create_engine('sqlite:///database.sqlite')
sm = sessionmaker(bind=engine)

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
            laufNr        = int(laufNrStr),
            projectId     = int(cells[0].replace("-", "") + laufNrStr),
            firma         = cells[2], 
            bereich       = cells[3], 
            geschlecht    = cells[4], 
            vorname       = cells[5], 
            nachname      = cells[6], 
            adresse_FA    = cells[7], 
            PLZ_FA        = plzNr,
            ort_FA        = cells[9], 
            tel_1         = cells[10],
            mobil         = cells[11], 
            fax           = cells[12], 
            auftragsort   = cells[13], 
            auftragsdatum = cells[14], 
            lfn           = int(cells[15])
        )
    except Exception as e:
        print(e)
        return None

    raise AssertionError("WTF")

def parseTable(table):
    for row in table.rows:

        # skip header row #
        if row.cells[0].text == HEADER_CELL_ZERO:
            continue

        cl = rowCellsToContractLocation(row.cells)
        if not cl:
            continue

        session = sm()
        session.merge(cl)
        session.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse a docx with a table database')
    parser.add_argument('FILE', nargs='+', help='The docx-file to parse')
    args = parser.parse_args()

    for f in args.FILE:
        document = docx.Document(f)
        ContractLocation.getBase().metadata.create_all(engine)

        for table in document.tables:
            parseTable(table)
