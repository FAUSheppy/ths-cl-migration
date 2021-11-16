from sqlalchemy import Column, Integer, String, Boolean, or_, and_
from sqlalchemy.orm import declarative_base
base   = declarative_base()

class ContractLocation(base):
    __tablename__ = "contract_locations"
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

def getBase():
    return base
