#!/usr/bin/python3

import argparse
import docx

from sqlalchemy import Column, Integer, String, Boolean, or_, and_
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func
import sqlalchemy

HEADER_CELL_ZERO = "Proj-Id"
engine = sqlalchemy.create_engine('sqlite:///test.sqlite')
base   = declarative_base()
sm = sessionmaker(bind=engine)

class ContractLocation(base):
    __tablename__ = "contract_locations"
    year          = Column(Integer)
    laufNr        = Column(Integer)
    projectId     = Column(Integer, primary_key=True)
    firma         = Column(String)
    bereich       = Column(String)
    geschlect     = Column(String)
    vorname       = Column(String)
    nachname      = Column(String)
    adresse_FA    = Column(String)
    PLZ_FA        = Column(Integer)
    ort_FA        = Column(String)
    tel_1         = Column(String)
    mobil         = Column(String)
    fax           = Column(String)
    auftragsort   = Column(String)
    auftragsdatum = Column(String)
    lfn           = Column(Integer)

def rowCellsToContractLocation(cells):
    cells = list([c.text.replace("-","") for c in cells])
    try:
        return ContractLocation(
            year          = int(cells[0]),
            laufNr        = int(cells[1]),
            projectId     = int(cells[0] + cells[1]),
            firma         = cells[2], 
            bereich       = cells[3], 
            geschlect     = cells[4], 
            vorname       = cells[5], 
            nachname      = cells[6], 
            adresse_FA    = cells[7], 
            PLZ_FA        = int(cells[8]), 
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
    finally:
        return None

def parseTable(table):
    for row in table.rows:

        # skip header row #
        if row.cells[0].text == HEADER_CELL_ZERO:
            continue

        cl = rowCellsToContractLocation(row.cells)
        if not cl:
            continue
        session = sm()
        session.add(cl)
        session.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse a docx with a table database')
    parser.add_argument('FILE', help='The docx-file to parse')
    args = parser.parse_args()

    document = docx.Document(args.FILE)
    base.metadata.create_all(engine)

    for table in document.tables:
        parseTable(table)
