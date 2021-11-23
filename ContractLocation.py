from sqlalchemy import Column, Integer, String, Boolean, or_, and_
from sqlalchemy.orm import declarative_base
base   = declarative_base()

class ContractLocation(base):
    __tablename__ = "contract_locations"
    lfn           = Column(Integer)
    projectid     = Column(Integer, primary_key=True)
    firma         = Column(String)
    bereich       = Column(String)
    geschlecht    = Column(String)
    vorname       = Column(String)
    nachname      = Column(String)
    adresse_fa    = Column(String)
    plz_fa        = Column(Integer)
    ort_fa        = Column(String)
    tel_1         = Column(String)
    mobil         = Column(String)
    fax           = Column(String)
    auftragsort   = Column(String)
    auftragsdatum = Column(String)
    date_parsed   = Column(Integer)

def getBase():
    return base
