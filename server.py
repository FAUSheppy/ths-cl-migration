#!/usr/bin/python3

import flask
import json
import argparse
import os
import datetime
import os.path
import werkzeug.utils

from sqlalchemy import Column, Integer, String, Boolean, or_, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func
import sqlalchemy
from flask_sqlalchemy import SQLAlchemy


app = flask.Flask("THS-ContractLocations")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

HEADER_NAMES = ["Jahr", "Lauf Nr.", "Project Id", "Firma", "Bereich",
                "Geschlecht", "Vorname", "Nachname", "Adresse FA",
                "PLZ FA", "Ort FA", "Telefon", "Mobil", "Fax", "Auftragsort",
                "LFN"]

@app.route("/", methods=["GET"])
def root():
    # TODO delete function
    # TODO add new dataset popup
    header = list(ContractLocation.__table__.columns.keys())
    return flask.render_template("index.html", headerCol=header, headerDisplayNames=HEADER_NAMES)

@app.route("/data-source", methods=["POST"])
def dataSource():
    dt = DataTable(flask.request.form.to_dict())
    jsonDict = dt.get()
    return flask.Response(json.dumps(jsonDict), 200, mimetype='application/json')

@app.before_first_request
def init():
    app.config["DB"] = db
    db.create_all()

    TRIGGER_FOR_SEARCHABLE_STRING_1 = '''
        CREATE TRIGGER IF NOT EXISTS populate_searchable_insert
            AFTER INSERT ON contract_locations
        BEGIN
            INSERT INTO searchHelper VALUES (
                NEW.projectId, ( 
                                    COALESCE(NEW.year,'')
                                 || COALESCE(NEW.firma,'')
                                 || COALESCE(NEW.projectId,'')
                                 || COALESCE(NEW.bereich,'')
                                 || COALESCE(NEW.vorname,'')
                                 || COALESCE(NEW.nachname,'')
                                 || COALESCE(NEW.adresse_FA,'')
                                 || COALESCE(NEW.PLZ_FA,'')
                                 || COALESCE(NEW.ort_FA,'')
                                 || COALESCE(NEW.tel_1,'')
                                 || COALESCE(NEW.mobil,'')
                                 || COALESCE(NEW.fax,'')
                                 || COALESCE(NEW.auftragsort,'')
                                 || COALESCE(NEW.auftragsdatum,'')
                              )
            );
        END;'''

    TRIGGER_FOR_SEARCHABLE_STRING_2 = '''
        CREATE TRIGGER IF NOT EXISTS populate_searchable_update
            AFTER UPDATE ON contract_locations
        BEGIN
            UPDATE searchHelper
                SET fullString = (
                                    COALESCE(NEW.year,'')
                                 || COALESCE(NEW.firma,'')
                                 || COALESCE(NEW.projectId,'')
                                 || COALESCE(NEW.bereich,'')
                                 || COALESCE(NEW.vorname,'')
                                 || COALESCE(NEW.nachname,'')
                                 || COALESCE(NEW.adresse_FA,'')
                                 || COALESCE(NEW.PLZ_FA,'')
                                 || COALESCE(NEW.ort_FA,'')
                                 || COALESCE(NEW.tel_1,'')
                                 || COALESCE(NEW.mobil,'')
                                 || COALESCE(NEW.fax,'')
                                 || COALESCE(NEW.auftragsort,'')
                                 || COALESCE(NEW.auftragsdatum,'')
                                )
                WHERE projectId = NEW.projectId;
        END;'''

    db.session.commit()
    db.session.execute(TRIGGER_FOR_SEARCHABLE_STRING_1)
    db.session.execute(TRIGGER_FOR_SEARCHABLE_STRING_2)
    print("Init Done")

class ContractLocation(db.Model):
    __tablename__ = "contract_locations"
    year          = Column(Integer)
    laufNr        = Column(Integer)
    projectId     = Column(Integer, primary_key=True)
    firma         = Column(String)
    bereich       = Column(String)
    geschlect    = Column(String)
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

    def toDict(self):
        tmpDict = dict(self.__dict__)
        tmpDict.pop("_sa_instance_state")
        return tmpDict

class SearchHelper(db.Model):
    __tablename__ = "searchHelper"
    projectId     = Column(Integer, primary_key=True)
    fullString    = Column(String)

class DataTable():
    
    def __init__(self, d):
        self.draw  = int(d["draw"])
        self.start = int(d["start"])
        self.length = int(d["length"])
        self.trueLength = -1
        self.searchValue = d["search[value]"]
        self.searchIsRegex = d["search[regex]"]

    def __build(self, results, total, filtered):

        self.cacheResults = results
        
        count = 0
        resultDicts = [ r.toDict() for r in results ]
        values = [ list(r.values()) for r in resultDicts ]
        #for r in resultDicts:
        #    r.update({ "DT_RowID"   : "row_{}".format(count) })
        #    r.update({ "DT_RowData" : { "pkey" : count }     })
        #    count += 1

        d = dict()
        d.update({ "draw" : self.draw })
        d.update({ "recordsTotal" : total })
        d.update({ "recordsFiltered" :  filtered })
        d.update({ "data" : values })

        return d

    def get(self):

        filtered = 0
        total    = 0

        # TODO more permissive multi word search #
        if self.searchValue:

            # search string #
            search        = "%{}%".format(self.searchValue)

            # base query
            query         = db.session.query(SearchHelper.projectId)
            total         = query.count()

            # filte query
            filterQuery   = query.filter(SearchHelper.fullString.like(search))
            projectIdList = filterQuery.all()
            filtered      = filterQuery.count()

            # get relevant pIds from searchHelper #
            projectIdList = filterQuery.offset(self.start).limit(self.length).all()

            # use pIds to retrive full information #
            results = []
            for pIdTup in projectIdList:
                pId = pIdTup[0]
                singleResult = db.session.query(ContractLocation).filter(
                                    ContractLocation.projectId == int(pId)).first()
                if singleResult:
                    results.append(singleResult)
        else:
            query    = db.session.query(ContractLocation)
            results  = query.offset(self.start).limit(self.length).all()
            total    = query.count()
            filtered = total


        return self.__build(results, total, filtered)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Start THS-Contract Locations')
    parser.add_argument('--interface', default="localhost", help='Interface to run on')
    parser.add_argument('--port', default="5000", help='Port to run on')
   
    
    args = parser.parse_args()
    app.run(host=args.interface, port=args.port)
