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
    return flask.render_template("index.html", headerCol=HEADER_NAMES)

@app.route("/data-source", methods=["POST"])
def dataSource():
    dt = DataTable(flask.request.form.to_dict())
    return flask.Response(json.dumps(dict()), 200, mimetype='application/json')

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
            UPDATE searchHelper where projectId = NEW.projectId
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
                                );
        END;'''

    triggerInsert = sqlalchemy.DDL(TRIGGER_FOR_SEARCHABLE_STRING_1)
    triggerUpdate = sqlalchemy.DDL(TRIGGER_FOR_SEARCHABLE_STRING_2)
    sqlalchemy.event.listen(ContractLocation, 'after_insert', triggerInsert)
    sqlalchemy.event.listen(ContractLocation, 'after_update', triggerUpdate)

class ContractLocation(db.Model):
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

class DataTable():
    
    def __init__(self, d):
        self.draw  = d["draw"]
        self.start = d["start"]
        self.length = d["length"]
        self.searchValue = d["search[value]"]
        self.searchIsRegex = d["search[regex]"]

    def __build(results, recordsTotal, recordsFiltered):
        d = dict()
        d.update({ "draw" : self.draw })
        d.update({ "recordsTotal" :  recordsTotal })
        d.update({ "recordsFiltered" :  recordsFiltered })
        d.update({ "data" : results })

    def get():
        if self.searchValue:
        results = db.session.query(ContractLocation)
        # query db here #

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Start THS-Contract Locations')
    parser.add_argument('--interface', default="localhost", help='Interface to run on')
    parser.add_argument('--port', default="5000", help='Port to run on')
   
    
    args = parser.parse_args()
    app.run(host=args.interface, port=args.port)
