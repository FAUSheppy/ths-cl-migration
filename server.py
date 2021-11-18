#!/usr/bin/python3

import flask
import json
import argparse
import os
import datetime
import os.path
import werkzeug.utils
import datetime
import samba
import mimetypes

from sqlalchemy import Column, Integer, String, Boolean, or_, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func
import sqlalchemy
from flask_sqlalchemy import SQLAlchemy

import flask_wtf as fwtf
import wtforms as forms
import wtforms.validators as validators

from constants import *
from formentry import FormEntry, formEntryArrayFromColNames

import filesystem
import filedetection

app = flask.Flask("THS-ContractLocations", static_folder=None)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "secret"
app.config['UPLOAD_FOLDER'] = "uploads/"
db = SQLAlchemy(app)

def getDbSchema():
    return list(ContractLocation.__table__.columns.keys())

@app.route('/entry-content', methods=['GET', 'POST'])
def entryContentBig():
    projectId = flask.request.args.get("projectId")
    colKeys = list(ContractLocation.__table__.columns.keys())
    
    # empty form if no project id #
    if not projectId:
        formEntries = formEntryArrayFromColNames(colKeys, None)
        return flask.render_template("entry-content-full.html", formEntries=formEntries)

    # look for project id in db #
    cl = db.session.query(ContractLocation).filter(ContractLocation.projectId == projectId).first()
    if not cl:
        return ("No such project", 404)
    else:
        # get column names #
        formEntries = formEntryArrayFromColNames(colKeys, cl)
        return flask.render_template("entry-content-full.html", entry=cl, formEntries=formEntries)

@app.route("/schema")
def schema():
    header = getDbSchema()
    return flask.Response(json.dumps(header), 200, mimetype="application/json")


@app.route('/file-list')
def fileList():
    projectId = flask.request.args.get("projectId")
    if not projectId:
        return ("", 200)
    files = db.session.query(AssotiatedFile).filter(AssotiatedFile.projectId == projectId).all()
    fileListItems = filesystem.itemsArrayFromDbEntries(files)
    if fileListItems:
        return flask.render_template("file-list.html", fileListItems=fileListItems)
    else:
        return ("", 200)

@app.route('/smb-file-list')
def smbFileList():
    projectId = flask.request.args.get("projectId")
    if not projectId:
        return ("", 200)

    files = None
    # check if path is known #
    pp = db.session.query(ProjectPath).filter(ProjectPath.projectId == projectId).first()
    if pp:
        files = samba.find(pp.sambaPath, None, 0, app, [], startInProjectDir=True, isFqPath=True)
        # delete db entry if fail #
        if not files:
            db.session.delete(pp)
            db.session.commit()

    # search for project if fail #
    if not files:
        cl = db.session.query(ContractLocation).filter(
                        ContractLocation.projectId == projectId).first()
        smbPath, projectDir, year = samba.buildPath(cl, app)

        # generate path keywords to speed up search #
        prioKeywords = [cl.nachname, cl.firma, cl.auftragsort]
        prioKeywords += list(filter(lambda x: len(x)>=3, cl.firma.split(" ")))
        prioKeywords = list(map(lambda s: s.strip().lower(), prioKeywords))

        # filter out keywords that are too common #
        prioKeywords = list(filter(lambda x: not x.lower() in ["gmbh"], prioKeywords))

        files = samba.find(smbPath, projectDir, year, app, prioKeywords)
    if not files:
        return ("Keine Netzwerkordner gefunden (gesucht wurde nach '{}' in '{}')".format(
                    projectDir, smbPath), 200)
    else:

        # record project dir #
        trueProjectDir = os.path.dirname(files[0])
        db.session.merge(ProjectPath(projectId=projectId, sambaPath=trueProjectDir))
        db.session.commit()

        # generate response
        fileListItems = samba.filesToFileItems(files)
        if fileListItems:
            return flask.render_template("file-list.html", fileListItems=fileListItems)
        else:
            return ("Keine weiteren Dateien im Netzwerk verfügbar", 200)

@app.route('/files', methods=['GET', 'POST', 'DELETE'])
def upload_file():
    projectId = flask.request.args.get("projectId")
    if flask.request.method == 'POST':
        if 'file' not in flask.request.files:
            flash('No file part')
            return redirect(flask.request.url)
        uploadFile = flask.request.files['file']
        if uploadFile.filename == '':
            flask.flash('No selected file')
            return flask.redirect(request.url)
        elif uploadFile:

            # build filename/path #
            filename      = werkzeug.utils.secure_filename(uploadFile.filename)
            projectIdSafe = werkzeug.utils.secure_filename(projectId)
            projectDir    = os.path.join(app.config["UPLOAD_FOLDER"], projectIdSafe)
            fullpath      = os.path.join(projectDir, filename)
            
            # create project directory if not exits #
            if not os.path.isdir(projectDir):
                os.mkdir(projectDir)

            # save file #
            uploadFile.save(fullpath)

            # try to determine contents of the file #
            fileType = filedetection.detectType(fullpath)

            # record file in database #
            db.session.merge(AssotiatedFile(fullpath=fullpath, sha512=0, 
                                projectId=projectIdSafe, fileType=fileType))
            db.session.commit()
            return ("", 204)
        else:
            return ("Bad Upload (POST) Request", 405)
    elif flask.request.method == 'GET':
        
        # get path arg #
        fullpath = flask.request.args.get("fullpath")
        if not fullpath:
            return ("Missing fullpath arg in URL", 405)
       
        # determine path type #
        isSamba = fullpath.startswith("\\\\")

        if isSamba:
            response = flask.make_response(samba.getFile(fullpath))
            response.headers.set('Content-Type', mimetypes.guess_type(fullpath))
            name = os.path.basename(fullpath)
            response.headers.set('Content-Disposition', 'attachment', filename=name)
            return response
        else:
            fileEntry = db.session.query(AssotiatedFile).filter(
                            AssotiatedFile.fullpath == fullpath).first()
            print(fileEntry)
            if fileEntry:
                relativePathInUploadDir = fileEntry.fullpath.replace(app.config["UPLOAD_FOLDER"], "")
                return flask.send_from_directory(app.config["UPLOAD_FOLDER"], relativePathInUploadDir)
    elif flask.request.method == 'DELETE':
        fullpath = flask.request.args.get("fullpath")
        fileEntry = db.session.query(AssotiatedFile).filter(
                        AssotiatedFile.fullpath == fullpath).first()
        if fileEntry:
            db.session.delete(fileEntry)
            # always use a secure path here !! (the db path is secure)#
            os.remove(fileEntry.fullpath)
            db.session.commit()
            return ("", 204)
        else:
            return ("No such file: {}".format(fullpath), 404)
    else:
        return ("{} not implemented".format(flask.request.method), 405)

@app.route("/", methods=["GET", "POST", "DELETE", "PATCH"])
def root():
    header = getDbSchema()
    if flask.request.method == "GET":
        return flask.render_template("index.html", headerCol=header, 
                                                    headerDisplayNames=HEADER_NAMES)
    elif flask.request.method == "POST":
        cl = ContractLocation()
        for col, name in zip(header, HEADER_NAMES):
            value = flask.request.form[col]
            if col in IS_INT_TYPE:
                if value == "":
                    value = 0
                else:
                    value = int(value)
            setattr(cl, col, value)
        db.session.merge(cl)
        db.session.commit()
        return ("", 204)
    elif flask.request.method == "DELETE":
        projectId = flask.request.form["id"]
        print(projectId)
        cl = db.session.query(ContractLocation).filter(
                        ContractLocation.projectId == projectId).first()
        if not cl:
            return ("No such project", 404)
        db.session.delete(cl)
        db.session.commit()
        return ("", 204)
    else:
        return (405, "{} not allowed".format(flask.request.method))
        

@app.route("/data-source", methods=["POST"])
def dataSource():
    cols = getDbSchema()
    dt = DataTable(flask.request.form.to_dict(), cols)
    jsonDict = dt.get()
    return flask.Response(json.dumps(jsonDict), 200, mimetype='application/json')

@app.route("/id-suggestions")
def curMaxSequenceNumber():
    order = db.session.query(ContractLocation.lfn).order_by(sqlalchemy.desc(ContractLocation.lfn))
    maxNr = order.first()[0] + 1
    if not maxNr:
        maxNr = 0

    today = datetime.datetime.today()
    monthId = today.month *   10000
    dayId   = today.day   * 1000000
    projectId = dayId + monthId + maxNr
    return flask.Response(json.dumps({ "max" : maxNr,  "projectId" : projectId }), 
                            200, mimetype='application/json')

@app.route("/new-document")
def newDocumentFromTemplate():
    projectId = flask.request.args.get("projectId")
    template = flask.request.args.get("template")
    if not projectId:
        return ("Missing projectId as URL-arg", 400)

    entry = db.session.query(ContractLocation).filter(
                    ContractLocation.projectId == projectId).first()
    if not entry:
        return ("Project not found", 404)

    if not template:
        documentTemplateList = filesystem.getTemplates()
        return flask.render_template("select_template.html", dtList=documentTemplateList,
                                        projectId=projectId)
    else:
        # TODO defenitly verify the path somehow
        name = "{}_{}.docx".format(os.path.basename(template).replace(".docx",""), projectId)
        instance = filesystem.getDocumentInstanceFromTemplate(template, projectId, entry.lfn)
        response = flask.make_response(instance)
        response.headers.set('Content-Type', MS_WORD_MIME)
        response.headers.set('Content-Disposition', 'attachment', filename=name)
        return response
        
@app.route('/static/<path:path>')
def send_js(path):
    response = flask.send_from_directory('static', path)
    #response.headers['Cache-Control'] = "max-age=2592000"
    return response

@app.before_first_request
def init():
    samba.initClient(app.config["SMB_SERVER"], app.config["SMB_USER"], app.config["SMB_PASS"], app)
    app.config["DB"] = db
    db.create_all()

    TRIGGER_FOR_SEARCHABLE_STRING_1 = '''
        CREATE TRIGGER IF NOT EXISTS populate_searchable_insert
            AFTER INSERT ON contract_locations
        BEGIN
            INSERT INTO searchHelper VALUES (
                NEW.projectId, ( 
                                    COALESCE(NEW.firma,'')
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
                                    COALESCE(NEW.firma,'')
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

class AssotiatedFile(db.Model):
    __tablename__ = "files"
    fullpath      = Column(String, primary_key=True)
    sha512        = Column(String)
    projectId     = Column(Integer)
    fileType      = Column(String)

class ContractLocation(db.Model):
    __tablename__ = "contract_locations"
    laufNr        = Column(Integer)
    projectId     = Column(Integer, primary_key=True)
    firma         = Column(String)
    bereich       = Column(String)
    geschlecht    = Column(String)
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

    def getColByNumber(self, nr):
        nr = int(nr)
        value = getattr(self, getDbSchema()[nr])
        return value

class SearchHelper(db.Model):
    __tablename__ = "searchHelper"
    projectId     = Column(Integer, primary_key=True)
    fullString    = Column(String)

class ProjectPath(db.Model):
    __tablename__ = "sambaPaths"
    projectId     = Column(Integer, primary_key=True)
    sambaPath     = Column(String)

class DataTable():
    
    def __init__(self, d, cols):
        self.draw  = int(d["draw"])
        self.start = int(d["start"])
        self.length = int(d["length"])
        self.trueLength = -1
        self.searchValue = d["search[value]"]
        self.searchIsRegex = d["search[regex]"]
        self.cols = cols
        self.orderByCol = int(d["order[0][column]"])
        self.orderDirection = d["order[0][dir]"]

        # order variable for use with pythong sorted etc #
        self.orderAsc = self.orderDirection == "asc"

        # oder variable for use with sqlalchemy
        if self.orderAsc:
            self.orderAscDbClass = sqlalchemy.asc
        else:
            self.orderAscDbClass = sqlalchemy.desc

    def __build(self, results, total, filtered):

        self.cacheResults = results
        
        count = 0
        resultDicts = [ r.toDict() for r in results ]

        # data list must have the correct order (same as table scheme) #
        rows = []
        for r in resultDicts:
            singleRow = []
            for key in self.cols:
                singleRow.append(r[key])
            rows.append(singleRow)

        d = dict()
        d.update({ "draw" : self.draw })
        d.update({ "recordsTotal" : total })
        d.update({ "recordsFiltered" :  filtered })
        d.update({ "data" : rows })

        return d

    def get(self):

        filtered = 0
        total    = 0

        if self.searchValue:

            # base query
            query         = db.session.query(SearchHelper.projectId)
            total         = query.count()

            # search string (search for all substrings individually #
            filterQuery = query
            for substr in self.searchValue.split(" "):
                searchSubstr = "%{}%".format(substr.strip())
                filterQuery  = filterQuery.filter(SearchHelper.fullString.like(searchSubstr))

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
                results = sorted(results, key=lambda cl: cl.getColByNumber(self.orderByCol), 
                                    reverse=not self.orderAsc)
        else:

            query    = db.session.query(ContractLocation)
            if self.orderByCol:
                query  = query.order_by(self.orderAscDbClass(
                                            list(ContractLocation.__table__.c)[self.orderByCol]))
            results  = query.offset(self.start).limit(self.length).all()
            total    = query.count()
            filtered = total


        return self.__build(results, total, filtered)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Start THS-Contract Locations')
    parser.add_argument('--interface', default="localhost", help='Interface to run on')
    parser.add_argument('--port', default="5000", help='Port to run on')

    parser.add_argument('--smbserver', help='SMB Server Target')
    parser.add_argument('--smbuser',   help='SMB User')
    parser.add_argument('--smbpass',   help='SMB Password')
    parser.add_argument('--smbshare', default="THS", help='SMB Password')

    args = parser.parse_args()

    app.config["SMB_SERVER"] = args.smbserver
    app.config["SMB_USER"]   = args.smbuser
    app.config["SMB_PASS"]   = args.smbpass
    app.config["SMB_SHARE"]  = args.smbshare

    app.run(host=args.interface, port=args.port)
