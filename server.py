#!/usr/bin/python3

import flask
import argparse
import glob
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

@app.route("/", methods=["GET", "POST"])
def root():
    return flask.render_template("index.html", listContent=allFiles)

@app.before_first_request
def init():
    app.config["DB"] = db
    db.create_all()

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

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Start THS-Contract Locations')
    parser.add_argument('--interface', default="localhost", help='Interface to run on')
    parser.add_argument('--port', default="5000", help='Port to run on')
   
    
    args = parser.parse_args()
    app.run(host=args.interface, port=args.port)
