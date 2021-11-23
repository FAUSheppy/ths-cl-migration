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
import psycopg2

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
import notifications
from flask_cors import CORS

app = flask.Flask("THS-ContractLocations", static_folder=None)
CORS(app)
app.config.from_object("config")
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite'
app.config['SECRET_KEY'] = "secret"
app.config['UPLOAD_FOLDER'] = "uploads/"
db = SQLAlchemy(app)

def getDbSchema(filterCols=False):
    cols = list(ContractLocation.__table__.columns.keys())
    if filterCols:
        return list(filter(lambda c: c not in COLS_IGNORE_LIST, cols))
    else:
        return cols

@app.route('/additional-dates', methods=["GET", "POST", "DELETE"])
def additionalDates():
    projectId = flask.request.args.get("projectId")
    additionalDatesObj = db.session.query(AdditionalDates).filter(
                                    AdditionalDates.projectid == projectId).first()

    # empty if no project id #
    if not projectId:
        return flask.render_template("additional-dates-section.html",
                                            additionalDates=[], freeFields=range(0, 10))
    projectId = int(projectId)

    if flask.request.method == "GET":
        dates = []
        if additionalDatesObj and additionalDatesObj.dates:
            for d in additionalDatesObj.dates.split(","):
                dates.append(datetime.datetime.strptime(
                                d, DB_DATE_FORMAT).strftime(HTML_DATE_FORMAT))

        return flask.render_template("additional-dates-section.html",
                                            additionalDates=dates,
                                            freeFields=range(len(dates), 10))
    elif flask.request.method == "POST":
        datesToSave = flask.request.json.get("dates")

        # append if an entry already exits #
        datesCurrent = ""
        if additionalDatesObj:
            datesCurrent = additionalDatesObj.dates

        if datesToSave:
            for d in datesToSave:
                datesCurrent += "," + datetime.datetime.strptime(
                                        d, HTML_DATE_FORMAT).strftime(DB_DATE_FORMAT)
            datesCurrent = datesCurrent.strip(",")
            db.session.merge(AdditionalDates(projectid=projectId, dates=datesCurrent))
            db.session.commit()
        else:
            return ("Not dates to save transmitted", 400)
    elif flask.request.method == "DELETE":
        if not additionalDatesObj:
            return ("No additional dates for this id", 404)
        else:
            db.session.delete(additionalDatesObj)
            db.session.commit()
    else:
        return ("Unsupported Method: {}".format(flask.request.method), 405)

@app.route('/submit-project-path', methods=['GET', 'POST', 'DELETE'])
def submitProjectPath():
    if flask.request.method == "POST":
        path = flask.request.json["path"].strip()
        projectId = int(flask.request.json["projectId"])

        # allow copied in paths #
        if path.startswith("T:"):
            replace = "T:"
            withThis  = "\\\\{}\\{}".format(app.config["SMB_SERVER"], app.config["SMB_SHARE"])
            path = path.replace(replace, withThis)

        # check the path #
        print("path:", path)
        try:
            files = samba.find(path, None, 0, app, [], startInProjectDir=True, isFqPath=True)
        except ValueError as e:
            response = flask.Response("Bad path: {}".format(e), 404, mimetype='application/json')
            return response
        if not files:
            response = flask.Response("Path does not exist", 404)
            return response
        else:
            db.session.merge(ProjectPath(projectId=projectId, sambapath=path))
            db.session.commit()
            response = flask.Response("", 204)
            return response

    elif flask.request.method == "DELETE":
        projectId = int(flask.request.json["projectId"])
        pp = db.session.query(ProjectPath).filter(ProjectPath.projectid == projectId).first()
        if pp:
            db.session.delete(pp)
            db.session.commit()
            response = flask.Response("", 204)
            return response
        else:
            response = flask.Response("No samba path in DB for this project-id", 404)
            return response
    else:
        return ("WHY THE FUCK IS THIS A GET REQUEST", 418)

@app.route('/entry-content', methods=['GET', 'POST'])
def entryContentBig():
    projectId = flask.request.args.get("projectId")
    colKeys = getDbSchema(filterCols=True)
    
    # empty form if no project id #
    if not projectId:
        formEntries = formEntryArrayFromColNames(colKeys, None)
        return flask.render_template("entry-content-full.html", formEntries=formEntries,
                                        additionalDatesObj=[])
    projectId = int(projectId)

    # look for project id in db #
    cl = db.session.query(ContractLocation).filter(ContractLocation.projectid == projectId).first()
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
    projectId = int(projectId)
    files = db.session.query(AssotiatedFile).filter(AssotiatedFile.projectid == projectId).all()
    fileListItems = filesystem.itemsArrayFromDbEntries(files)
    if fileListItems:
        return flask.render_template("file-list.html", fileListItems=fileListItems)
    else:
        return ("", 200)

@app.route('/smb-file-list')
def smbFileList():

    # check samba enabled #
    if not app.config["SAMBA"]:
        return ("", 204)

    projectId = flask.request.args.get("projectId")
    if not projectId:
        return ("", 200)
    projectId = int(projectId)

    files = None
    dbPathEmpty = False

    # check if path is known #
    pp = db.session.query(ProjectPath).filter(ProjectPath.projectid == projectId).first()
    if pp:
        print("Found cached path {}".format(pp.sambapath))
        dbPathEmpty = not bool(pp.sambapath)
        if pp.sambapath:
            files = samba.find(pp.sambapath, None, 0, app, [], 
                                    startInProjectDir=True, isFqPath=True)
             # delete db entry if fail #
            if not files:
                pp.sambapath == ""
                db.session.merge(pp)
                db.session.commit()

    # search for project if fail #
    cl = db.session.query(ContractLocation).filter(
                    ContractLocation.projectid == projectId).first()
    if not cl:
        return ("No project for this ID", 404)

    # generate path and pdir #
    smbPath, projectDir, year = samba.buildPath(cl, app)

    # check in the static index for the pdir #
    sppi = db.session.query(StaticProjectPathIndex).filter(
                    StaticProjectPathIndex.dirname == projectDir).first()
    if sppi:
        print("Found entry in static index, trying: {}".format(sppi.fullpath))
        files = samba.find(sppi.fullpath, None, 0, app, [], startInProjectDir=True, isFqPath=True)

    # generate path keywords to speed up search #
    prioKeywords = [cl.nachname, cl.firma, cl.auftragsort]
    prioKeywords += list(filter(lambda x: len(x)>=3, cl.firma.split(" ")))
    prioKeywords = list(map(lambda s: s.strip().lower(), prioKeywords))

    # filter out keywords that are too common #
    prioKeywords = list(filter(lambda x: not x.lower() in ["gmbh"], prioKeywords))

    if not files and not dbPathEmpty:
        files = samba.find(smbPath, projectDir, year, app, prioKeywords)

    if not files:
        db.session.merge(ProjectPath(projectid=projectId, sambapath=""))
        db.session.commit()
        return flask.render_template("samba-file-not-found.html", projectDir=projectDir,
                                        searchPath=smbPath, keywords=prioKeywords,
                                        projectId=projectId,
                                        showResetButton=dbPathEmpty)
    else:

        # record project dir #
        trueProjectDir = os.path.dirname(files[0])
        db.session.merge(ProjectPath(projectid=projectId, sambapath=trueProjectDir))
        print("Recorded {} for {}".format(trueProjectDir, projectId))
        db.session.commit()

        # generate response
        fileListItems = samba.filesToFileItems(files)
        if fileListItems:
            replace  = "\\\\{}\\{}".format(app.config["SMB_SERVER"], app.config["SMB_SHARE"])
            withThis = "T:"
            displayPath = trueProjectDir.replace("/", "\\").replace(replace, withThis)
            return flask.render_template("file-list.html", fileListItems=fileListItems,
                                            basePath=displayPath)
        else:
            return ("Keine weiteren Dateien im Netzwerk verfügbar", 200)

@app.route('/files', methods=['GET', 'POST', 'DELETE'])
def upload_file():

    projectId = flask.request.args.get("projectId")
    if not projectId:
        return ("", 204)
    projectId = int(projectId)

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
            projectIdSafe = werkzeug.utils.secure_filename(str(projectId))
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
    header = getDbSchema(filterCols=True)
    if flask.request.method == "GET":
        render = flask.render_template("index.html", headerCol=header, 
                                                    headerDisplayNames=HEADER_NAMES)
        response = flask.Response(render, 200)
        response.headers.add('Access-Control-Allow-Headers', '*')
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    elif flask.request.method == "POST":
        
        # prepare new/updated entry #
        cl = ContractLocation()

        # handle standard fields #
        for col, name in zip(header, HEADER_NAMES):
            value = flask.request.form[col]

            # handle datatypes #
            if col in IS_INT_TYPE:
                if value == "":
                    value = 0
                else:
                    value = int(value)
            elif col in IS_DATE_TYPE:
                parsed = datetime.datetime.strptime(value, HTML_DATE_FORMAT)
                value  = parsed.strftime(DB_DATE_FORMAT)
                setattr(cl, "date_parsed", parsed.timestamp())

            # set value in class #
            setattr(cl, col, value)

        # handle additional dates-fields #
        additionalDatesFields = ["additional-date-{}".format(x) for x in range(0, 10)]
        newAdditionalDatesString = ""
        for key in additionalDatesFields:
            value = flask.request.form[key]
            if value:
                value = datetime.datetime.strptime(value, HTML_DATE_FORMAT).strftime(DB_DATE_FORMAT)
                newAdditionalDatesString += value + ","

        # remember old value for notification #
        oldCl = db.session.query(ContractLocation).filter(
                        ContractLocation.projectid == cl.projectid).first()
        oldAd = db.session.query(AdditionalDates).filter(
                        AdditionalDates.projectid == cl.projectid).first()

        # detach records #
        db.session.expunge_all()

        # merge additional dates into db #
        newAdditionalDatesString = newAdditionalDatesString.strip(",")
        ad = AdditionalDates(projectid=cl.projectid, dates=newAdditionalDatesString)
        db.session.merge(ad)

        # merge contract location main entry and commit #
        db.session.merge(cl)
        db.session.commit()

        # get all data from db and send notification #
        if app.config["SEND_NOTIFICATION"]:
            newCl = db.session.query(ContractLocation).filter(
                                ContractLocation.projectid == cl.projectid).first()
            newAd = db.session.query(AdditionalDates).filter(
                                AdditionalDates.projectid == cl.projectid).first()
            
            content = notifications.makeRepresentation(oldCl, oldAd, newCl, newAd)
            notifications.sendSignal(content, app)
        
        return ("", 204)

    elif flask.request.method == "DELETE":
        projectId = int(flask.request.form["id"])

        # delete the contract location entry #
        cl = db.session.query(ContractLocation).filter(
                        ContractLocation.projectid == projectId).first()
        if not cl:
            return ("No such project", 404)
        else:
            db.session.delete(cl)
        
        # delete the search helper #
        sh = db.session.query(SearchHelper).filter(SearchHelper.projectid == projectId).first()
        if sh:
            db.session.delete(sh)

        # delete the path if exits #
        pp = db.session.query(ProjectPath).filter(ProjectPath.projectid == projectId).first()
        if pp:
            db.session.delete(pp)

        # commit changes #
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
    yearId = today.year *   10000
    monthId = today.month   * 1000000
    projectId = yearId + monthId + maxNr
    return flask.Response(json.dumps({ "max" : maxNr,  "projectId" : projectId }), 
                            200, mimetype='application/json')

@app.route("/new-document")
def newDocumentFromTemplate():

    projectId = flask.request.args.get("projectId")
    template = flask.request.args.get("template")
    documentTemplateDict = filesystem.getTemplates()
    saveToSamba = bool(flask.request.args.get("saveToSamba"))

    if not projectId:
        return ("Missing projectId as URL-arg", 400)
    projectId = int(projectId)

    entry = db.session.query(ContractLocation).filter(
                    ContractLocation.projectid == projectId).first()
    if not entry:
        return ("Project not found", 404)

    if not template:

        # check if a project path is availiable #
        pp = db.session.query(ProjectPath).filter(ProjectPath.projectid == projectId).first()
        projectPathAvailiable = False
        if pp and app.config["SAMBA"]:
            projectPathAvailiable = bool(pp.sambapath)

        return flask.render_template("select_template.html",
                                        templatesDict=documentTemplateDict,
                                        projectId=projectId,
                                        projectPathAvailiable=projectPathAvailiable)
    else:
        if not template in documentTemplateDict:
            return ("Template not found", 404)
        else:
            path = os.path.join(app.config["DOC_TEMPLATE_PATH"], template)
           
            #  get instance of template #
            instance = filesystem.getDocumentInstanceFromTemplate(path, projectId, entry.lfn, app)

            if saveToSamba:
                pp = db.session.query(ProjectPath).filter(ProjectPath.projectid == projectId)
                if pp and pp.sambapath:
                    error = samba.carefullySaveFile(instance, pp.sambapath)
                    if error:
                        return ("Fehler beim Speichern: {}".format(error), 510)
                    else:
                        return ("Abgespeichert in {}".format(path), 200)
                    
                else:
                    return ("Fehler: Projekt nicht mehr mit einem Pfad assoziert", 404)
            else:
                response = flask.make_response(instance)
                response.headers.set('Content-Type', MS_WORD_MIME)
                retFname = "P-" + str(projectId) + "-" + template
                response.headers.set('Content-Disposition', 'attachment', filename=retFname)
                return response

@app.route('/static/<path:path>')
def send_js(path):
    response = flask.send_from_directory('static', path)
    #response.headers['Cache-Control'] = "max-age=2592000"
    return response

@app.before_first_request
def init():
    try:
        samba.initClient(app.config["SMB_SERVER"], app.config["SMB_USER"],
                            app.config["SMB_PASS"], app)
        app.config["SAMBA"] = True
    except AttributeError as e:
        print("Cannot init samba client: {}".format(e))
        app.config["SAMBA"] = False
    
    app.config["DB"] = db
    db.create_all()
   
    if "sqlite" in app.config["SQLALCHEMY_DATABASE_URI"]:
        from sqlitetrigger import TRIGGER_FOR_SEARCHABLE_STRING_1, TRIGGER_FOR_SEARCHABLE_STRING_2
    elif "postgresql" in app.config["SQLALCHEMY_DATABASE_URI"]:
        from psqltrigger import TRIGGER_FOR_SEARCHABLE_STRING_1, TRIGGER_FOR_SEARCHABLE_STRING_2
    else:
        raise ValueError("No supported database string (sqlite or postgresql")

    db.session.commit()
    db.session.execute(TRIGGER_FOR_SEARCHABLE_STRING_1)
    db.session.execute(TRIGGER_FOR_SEARCHABLE_STRING_2)
    print("Init Done")

class AssotiatedFile(db.Model):
    __tablename__ = "files"
    fullpath      = Column(String, primary_key=True)
    sha512        = Column(String)
    projectid     = Column(Integer)
    fileType      = Column(String)

class AdditionalDates(db.Model):
    __tablename__ = "additional_dates"
    projectid     = Column(Integer, primary_key=True)
    dates         = Column(String)

class ContractLocation(db.Model):
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

    def toDict(self):
        tmpDict = dict(self.__dict__)
        for keysToIgnore in COLS_IGNORE_LIST:
            tmpDict.pop(keysToIgnore)
        return tmpDict

    def getColByNumber(self, nr):
        nr = int(nr)
        value = getattr(self, getDbSchema()[nr])
        return value

class SearchHelper(db.Model):
    __tablename__ = "search_helper"
    projectid     = Column(Integer, primary_key=True)
    fullString    = Column(String)

class ProjectPath(db.Model):
    __tablename__ = "samba_paths"
    projectid     = Column(Integer, primary_key=True)
    sambapath     = Column(String)

class StaticProjectPathIndex(db.Model):
    __tablename__ = "project_paths"
    dirname       = Column(String, primary_key=True)
    fullpath      = Column(String)

class DataTable():
    
    def __init__(self, d, cols):
        self.draw  = int(d["draw"])
        self.start = int(d["start"])
        self.length = int(d["length"])
        self.trueLength = -1
        self.searchValue = d["search[value]"]
        self.searchIsRegex = d["search[regex]"]
        self.cols = getDbSchema(filterCols=True)
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
            query         = db.session.query(SearchHelper.projectid)
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
                                    ContractLocation.projectid == int(pId)).first()
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

        # query additional dates #
        for r in results:
            additionalDatesObj = db.session.query(AdditionalDates).filter(
                                    AdditionalDates.projectid == r.projectid).first()
           
            if additionalDatesObj and additionalDatesObj.dates:
                r.auftragsdatum += ", " + additionalDatesObj.dates.replace(",", ", ")


        return self.__build(results, total, filtered)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Start THS-Contract Locations')
    parser.add_argument('--interface', default="localhost", help='Interface to run on')
    parser.add_argument('--port', default="5000", help='Port to run on')

    parser.add_argument('--smbserver', help='SMB Server Target')
    parser.add_argument('--smbuser',   help='SMB User')
    parser.add_argument('--smbpass',   help='SMB Password')
    parser.add_argument('--smbshare',  default="THS", help='SMB Password')

    args = parser.parse_args()

    #app.config["SMB_SERVER"] = args.smbserver
    #app.config["SMB_USER"]   = args.smbuser
    #app.config["SMB_PASS"]   = args.smbpass
    #app.config["SMB_SHARE"]  = args.smbshare

    #app.config["DOC_TEMPLATE_PATH"] = "document-templates"

    app.run(host=args.interface, port=args.port)
