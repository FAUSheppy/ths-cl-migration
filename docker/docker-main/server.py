#!/usr/bin/python3

import flask
import json
import argparse
import os
import datetime
import os.path
import werkzeug.utils
import datetime
import samba_mounted_fs
import samba_mounted_fs as fsbackend
import mimetypes
import psycopg2
import traceback
import sys

from sqlalchemy import Column, Integer, String, Boolean, or_, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func, text
import sqlalchemy
from flask_sqlalchemy import SQLAlchemy

import error
from constants import *
from formentry import FormEntry, formEntryArrayFromColNames

import filesystem
import filedetection
import notifications
import bwa
from flask_cors import CORS

app = flask.Flask("THS-ContractLocations", static_folder=None)
CORS(app)
app.config.from_object("config")
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite'
app.config['SECRET_KEY'] = "secret"
app.config['UPLOAD_FOLDER'] = "uploads/"
db = SQLAlchemy(app)

DATE_COL = 11

# debug logging #
# import logging
# logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

def getDbSchema(filterCols=False):
    cols = list(ContractLocation.__table__.columns.keys())
    if filterCols:
        return list(filter(lambda c: c not in COLS_IGNORE_LIST, cols))
    else:
        return cols

@app.route('/additional-dates', methods=["GET", "POST", "DELETE"])
def additionalDates():
    projectId = flask.request.args.get("projectId")

    # empty if no project id #
    if not projectId:
        return flask.render_template("additional-dates-section.html",
                                            additionalDates=[], freeFields=range(0, 10))
    projectId = int(projectId)
    additionalDatesObj = db.session.query(AdditionalDates).filter(
                                    AdditionalDates.projectid == projectId).first()

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
            files = fsbackend.listFiles(path)
        except ValueError as e:
            response = flask.Response("Bad path: {}".format(e), 404, mimetype='application/json')
            return response
        if not files:
            response = flask.Response("Path does not exist", 404)
            return response
        else:
            db.session.merge(ProjectPath(projectid=projectId, projectpath=path))
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

@app.route('/smb-file-list')
def smbFileList():

    projectId = flask.request.args.get("projectId")
    if not projectId:
        return ("", 200)
    projectId = int(projectId)

    files = None
    dbPathEmpty = True

    # check if path is known #
    pp = db.session.query(ProjectPath).filter(ProjectPath.projectid == projectId).first()
    fullpath = None
    if pp and not pp == "":
        print("Found cached path '{}'".format(pp.projectpath))
        dbPathEmpty = not bool(pp.projectpath)
        if pp.projectpath:
            fullpath = filesystem.addBasePath(pp.projectpath)
            try:
                files = fsbackend.listFiles(fullpath)
            except ValueError:
                # delete db entry if fail #
                if not files:
                    pp.projectpath = ""
                    db.session.merge(pp)
                    db.session.commit()
                    dbPathEmpty = True

    # search for project if fail #
    cl = db.session.query(ContractLocation).filter(
                    ContractLocation.projectid == projectId).first()
    if not cl:
        return ("No project for this ID", 404)

    # generate path and pdir #
    searchPath, projectDir, year = fsbackend.buildPath(cl)

    trueProjectDir = None
    if dbPathEmpty:
        trueProjectDir = fsbackend.find(projectDir, year)
    else:
        trueProjectDir = fullpath

    if not trueProjectDir:
        db.session.merge(ProjectPath(projectid=projectId, projectpath=""))
        db.session.commit()

        # fix search path for client display
        clientSearchPathDisplay = searchPath.replace(app.config["FILESYSTEM_PROJECTS_BASE_PATH"],
                                                     app.config["CLIENT_PATH_PREFIX"])

        return flask.render_template("samba-file-not-found.html", projectDir=projectDir,
                                        searchPath=clientSearchPathDisplay,
                                        projectId=projectId,
                                        showResetButton=dbPathEmpty)
    else:
        pathForDb = filesystem.removeBasePath(trueProjectDir)
        db.session.merge(ProjectPath(projectid=projectId, projectpath=pathForDb))
        db.session.commit()

        print("Recorded {} for {}".format(trueProjectDir, projectId))

        # generate response
        filesInProjectDir = fsbackend.listFiles(trueProjectDir)
        if not filesInProjectDir:
            return ("Keine Dateien vorhanden", 200)

        fileListItems = sorted([ filesystem.FileItem(path) for path in filesInProjectDir ])

        # fix client display path
        clientBasePathDisplay = trueProjectDir.replace(app.config["FILESYSTEM_PROJECTS_BASE_PATH"],
                                                     app.config["CLIENT_PATH_PREFIX"])

        return flask.render_template("file-list.html", fileListItems=fileListItems,
                                        basePath=clientBasePathDisplay,
                                        localfile=app.config["LOCAL_FILE_ID"])

@app.route('/files', methods=['GET'])
def files():

    projectId = flask.request.args.get("projectId")
    fullpath = flask.request.args.get("fullpath")
    if not fullpath:
        return ("Missing fullpath arg in URL", 405)
  
    # determine path type #
    isSamba = fullpath.startswith("\\\\")

    if isSamba:
        response = flask.make_response(fsbackend.getFile(fullpath))
        response.headers.set('Content-Type', mimetypes.guess_type(fullpath))
        name = os.path.basename(fullpath)
        response.headers.set('Content-Disposition', 'attachment', filename=name)
        return response
    else:
        dirname = os.path.dirname(fullpath).rstrip("/")
        print("Request from directory:", fullpath, dirname)
        pp = db.session.query(ProjectPath).filter(ProjectPath.projectpath==dirname).first()
        if pp:
            fqPath = os.path.join(flask.current_app.config["FILESYSTEM_PROJECTS_BASE_PATH"],
                                    dirname)
            return flask.send_from_directory(fqPath, os.path.basename(fullpath))
        else:
            return ("Pfad nicht in Projektordner. Zugriff Verweigert", 400)
        
@app.route("/modifying")
def isBeingModifyed():
    
    pid = flask.request.args.get("pid")
    lockRequester = flask.request.args.get("src")
    
    if not pid:
        return ("Missing PID Parameter", 406)
    elif not lockRequester:
        return ("Missing SRC Parameter", 406)
        
    filterQuery = db.session.query(ModStatus).filter(ModStatus.projectid == int(pid))
    orderQuery  = filter.order_by(sqlalchemy.desc(ModStatus.lastRenew))
    
    for modstatus in orderQuery.all():
        parsed = datetime.datetime.fromtimestamp(modstatus.lastRenew)
        if datetime.datetime.now() - parsed > datetime.timedelta(seconds=10):
            db.session.delete(modstatus)
            db.session.commit()
            continue
        elif modstatus.lockHolder == src:
            break;
        else:
            return (modstatus.lockHolder, 200) # inform client he is not lockholder
            
    db.session.merge(ModStatus(pid, datetime.datetime.now().timestamp(), src))
    db.session.commit()
    
    return ("",  204) # all ok, no or only outdated entries
            
    

@app.route("/", methods=["GET", "POST", "DELETE", "PATCH"])
def root():
    header = getDbSchema(filterCols=True)
    if flask.request.method == "GET":
        render = flask.render_template("index.html", headerCol=header, 
                                        headerDisplayNames=HEADER_NAMES,
                                        isTemplateIdent=str(IS_TEMPLATE_IDENT))
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

            # allow human readable projectId as input
            if col == "projectid":
                value = value.replace("P", "").replace("-", "")

            # handle datatypes #
            if col in IS_INT_TYPE:
                if value.strip() == "":
                    value = 0
                else:
                    try:
                        value = int(value)
                    except ValueError:
                        return ("{} erwartet eine Zahl oder ein leeres Feld. [{}]".format(col, value), 400)
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

@app.route("/entry-suggestions", methods=["POST"])
def entrySuggestionQuery():
    
    # CAREFULL HERE: DONT USE UNCHECKED SQL             #
    # "key" is only safe to use if in IS_TEMPLATE_IDENT #
    paramStringSafe = ""
    data = dict()
    for key, value in flask.request.form.items():
        if key in IS_TEMPLATE_IDENT:
            paramStringSafe += "{key} LIKE :{key} AND ".format(key=key)
            data.update({key : "%{}%".format(value)})

    # check if empty #
    if len(data) == 0:
        return ("", 204)

    sqlRaw = '''
        SELECT * FROM (
            SELECT COUNT(*) AS dupcount, firma, bereich, geschlecht,
                   vorname, nachname, adresse_fa, plz_fa, ort_fa, 
                   tel_1, mobil, fax 
            FROM contract_locations 
            WHERE {}
            GROUP BY firma, bereich, geschlecht, vorname, nachname,
                     adresse_fa, plz_fa, ort_fa, tel_1, mobil, fax
            ) AS sub
        ORDER BY sub.dupcount DESC;
    '''.format(paramStringSafe.rstrip("AND "))
    
    # execute #
    query = db.session.execute(text(sqlRaw), data)
    hit = query.first()
    
    # handle restuls #
    if hit:
        mapping = dict(hit._mapping)
        mapping.pop("dupcount")
        return flask.Response(json.dumps(mapping), 200, mimetype='application/json')
    else:
        return ("", 204)

@app.route("/data-source", methods=["POST"])
def dataSource():
    cols = getDbSchema(filterCols=True)

    # do not display certain fields in main data-table #
    cols = list(filter(lambda x: x not in ["tel_1", "mobil", "fax"], cols))
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
    yearId  = (today.year%100) * 1000000
    monthId = today.month * 10000
    projectId = yearId + monthId + maxNr

    projectIdColoq = "P-{:02d}{:02d}-{:04d}".format(today.year % 100, today.month, maxNr)
    return flask.Response(json.dumps({ "max" : maxNr, 
                            "projectIdNumneric" : projectId,
                            "projectIdColoq" : projectIdColoq }), 
                                200, mimetype='application/json')


@app.route("/bwa", methods=["GET", "POST"])
def bwaFunction():
    return bwa.bwa()

@app.route("/new-document")
def newDocumentFromTemplate():

    projectId = flask.request.args.get("projectId")
    template  = flask.request.args.get("template")
    noFilter  = flask.request.args.get("nofilter") == "true"
    reports   = flask.request.args.get("reports")  == "true"
    
    documentTemplateDict = filesystem.getTemplates()
    directSave = bool(flask.request.args.get("directSave"))

    yearFilter = ""
    if reports:
        documentTemplateDict = filesystem.getTemplates("reports")
    elif projectId.startswith("22") and not noFilter and not template:
        yearFilter = "Vorlagen für Jahr: 2022"
        deleteList = []
        for key, value in documentTemplateDict.items():
            if value.get("year") and value.get("year") != 2022:
                deleteList.append(key)

        for el in deleteList:
            documentTemplateDict.pop(el)

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
        if pp and (app.config["SAMBA"] or app.config["FILESYSTEM_PROJECTS_BASE_PATH"]):
            projectPathAvailiable = bool(pp.projectpath)

        templatesKeysSorted = sorted(documentTemplateDict.keys(), key=str.casefold)
        return flask.render_template("select_template.html",
                                        templatesKeysSorted=templatesKeysSorted,
                                        templatesDict=documentTemplateDict,
                                        projectId=projectId,
                                        projectPathAvailiable=projectPathAvailiable,
                                        yearFilter=yearFilter,
                                        reports=reports,
                                        reportsJsBool=str(reports).lower())
    else:
        if not template in documentTemplateDict:
            return ("Template not found", 404)
        else:
            # handle reports subdir
            reportsPath = ""
            if reports:
                reportsPath = "reports"

            pidPrettyString = str(projectId)
            if len(pidPrettyString) == 8:
                pidPrettyString = pidPrettyString[:4] + "-" +pidPrettyString[4:]
            if reports:
                retFname = app.config["REPORTS_FILENAME_PREFIX"] + pidPrettyString + "-" + template
            else:
                retFname = app.config["INVOICE_FILENAME_PREFIX"] + pidPrettyString + "-" + template

            path = os.path.join(app.config["DOC_TEMPLATE_PATH"], reportsPath, template)
           
            #  get instance of template #
            instance = filesystem.getDocumentInstanceFromTemplate(path, projectId, entry.lfn, app)
            if directSave:
                pp = db.session.query(ProjectPath).filter(
                                        ProjectPath.projectid == projectId).first()
                if pp and pp.projectpath:
                    path, error = fsbackend.carefullySaveFile(instance, 
                                        os.path.join(pp.projectpath, retFname))
                    if error:
                        return (error, 403)

                    displayPath = path.replace(app.config["FILESYSTEM_PROJECTS_BASE_PATH"],
                                               app.config["CLIENT_PATH_PREFIX"])

                    return ("OK: {}".format(displayPath), 200)
                else:
                    return ("Fehler: Projekt nicht mehr mit einem Pfad assoziert", 404)
            else:
                response = flask.make_response(instance)
                response.headers.set('Content-Type', MS_WORD_MIME)
                response.headers.set('Content-Disposition', 'attachment', filename=retFname)
                return response

@app.route('/static/<path:path>')
def send_js(path):
    response = flask.send_from_directory('static', path)
    #response.headers['Cache-Control'] = "max-age=2592000"
    return response

@app.route('/defaultFavicon.ico')
def icon():
    return flask.send_from_directory('static', 'defaultFavicon.ico')

ENDPOINTS = ["newDocumentFromTemplate", "smbFileList", "submitProjectPath", "upload_file"]
@app.before_request
def beforeRequest():
    if flask.request.endpoint in ENDPOINTS and app.config["SAMBA"]:
        fsbackend.deleteClient(app)
        try:
            fsbackend.initClient(app.config["SMB_SERVER"], app.config["SMB_USER"],
                                app.config["SMB_PASS"], app)
            app.config["SAMBA"] = True
        except AttributeError as e:
            print("Cannot init samba client: {}".format(e))
            app.config["SAMBA"] = False

@app.after_request
def afterRequest(response):
    if flask.request.endpoint in ENDPOINTS and app.config["SAMBA"]:
        fsbackend.deleteClient(app)
    return response

#@app.errorhandler(Exception)
#def errorhandler(e):
#    error.log(e)
#    return (504, str(e))

@app.before_first_request
def init():
    app.config["DB"] = db
    db.create_all()
  
    from sqlitetrigger import DOCUMENT_VIEW
    if "sqlite" in app.config["SQLALCHEMY_DATABASE_URI"]:
        from sqlitetrigger import TRIGGER_FOR_SEARCHABLE_STRING_1, TRIGGER_FOR_SEARCHABLE_STRING_2
    elif "postgresql" in app.config["SQLALCHEMY_DATABASE_URI"]:
        from psqltrigger import TRIGGER_FOR_SEARCHABLE_STRING_1, TRIGGER_FOR_SEARCHABLE_STRING_2
    else:
        raise ValueError("No supported database string (sqlite or postgresql")

    # must commit tables before adding triggers #
    db.session.commit()

    db.session.execute(sqlalchemy.sql.text(TRIGGER_FOR_SEARCHABLE_STRING_1))
    db.session.execute(sqlalchemy.sql.text(TRIGGER_FOR_SEARCHABLE_STRING_2))
    db.session.execute(sqlalchemy.sql.text(DOCUMENT_VIEW))

    db.session.commit()
    print("Init Done")

class ModStatus(db.Model):
    __tablename__ = "modification_status"
    projectid     = Column(Integer, primary_key=True)
    lastRenew     = Column(Integer)
    lockHolder    = Column(String)
    
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

        if nr == DATE_COL:
            try:
                return datetime.datetime.strptime(self.auftragsdatum, DB_DATE_FORMAT)
            except ValueError:
                return datetime.datetime.now() - datetime.timedelta(hours=24*365*100)

        value = getattr(self, getDbSchema()[nr])
        return value

    def getBwaCol(self, col):
        if col == 0:
            return str(self.projectid)[:4]
        elif col == 1:
            return self.lfn
        elif col == 2: # auftraggeber
            if self.firma:
                return self.firma
            else:
                return "{} {} {}".format(self.geschlecht, self.vorname, self.nachname)
        elif col == 3: # type, TODO from filesystem
            return "" 
        elif col == 4:
            return self.auftragsdatum
        elif col == 5: # netto
            return "" # TODO from filsystem
        elif col == 6: # brutto
            return "" # TODO from filsystem
        elif col == 7:
            return ""
        elif col == 8:
            return ""
        else:
            return ""

    def getProjectYear(self):
        year = None
        try:
            year = datetime.datetime.strptime(self.auftragsdatum, DB_DATE_FORMAT).year
        except ValueError:
            year = 2000 + int(str(self.projectid)[-7:-5])
            print("Failed to parse date correctly, assuming {} form projectId".format(year))
            if year < 2008:
                try: 
                    year = int(cl.auftragsdatum.split(".")[-1])
                    print("Too early, try maleformed date anyway, got {}".format(year))
                except ValueError as e:
                    print("Unparsable, cannot determine path: {}".format(e))
                    raise e
        return year

    def getProjectDir(self):
        '''Find the expected project dir'''
        
        nrStr = str(self.projectid)

        if self.getProjectYear() < 2020:
            endIdent = nrStr[-5:]
            yearIdent = nrStr[-7:-5]
            monthIdent = nrStr[:-7]
            if len(monthIdent) == 1:
                monthIdent = "0" + monthIdent
            projectDir  = "P-{month}-{year}-{end}".format(month=monthIdent, year=yearIdent, 
                                                                end=endIdent)
        else:
            lfn = nrStr[-4:]
            dt  = nrStr[:-4]
            assert len(dt) >= 3
            if len(dt) == 3:
                dt = "0" + dt
            projectDir  = "P-{}-{}".format(dt, lfn)

        return projectDir

class SearchHelper(db.Model):
    __tablename__ = "search_helper"
    projectid     = Column(Integer, primary_key=True)
    fullstring    = Column(String)

class ProjectPath(db.Model):
    __tablename__ = "project_paths"
    projectid     = Column(Integer, primary_key=True)
    projectpath   = Column(String)

class StaticProjectPathIndex(db.Model):
    __tablename__ = "static_project_paths"
    dirname       = Column(String, primary_key=True)
    fullpath      = Column(String)

class DataTable():
    
    def __init__(self, d, cols=None):
        self.draw  = int(d["draw"])
        self.start = int(d["start"])
        self.length = int(d["length"])
        self.trueLength = -1
        self.searchValue = d["search[value]"]
        self.searchIsRegex = d["search[regex]"]
        self.cols = cols or getDbSchema(filterCols=True)
        self.orderByCol = int(d["order[0][column]"])
        self.orderDirection = d["order[0][dir]"]

        # order by date during search rather than lfn #
        if self.orderByCol == 0 and self.searchValue:
            self.orderByCol = DATE_COL # auftragsdatum
            self.orderDirection = "desc"

        # order variable for use with pythong sorted etc #
        self.orderAsc = self.orderDirection == "asc"

        # oder variable for use with sqlalchemy
        if self.orderAsc:
            self.orderAscDbClass = sqlalchemy.asc
            self.orderAscDbClassReverse = sqlalchemy.desc
        else:
            self.orderAscDbClass = sqlalchemy.desc
            self.orderAscDbClassReverse = sqlalchemy.asc


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
                filterQuery  = filterQuery.filter(SearchHelper.fullstring.like(searchSubstr))

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
            else:
                query  = query.order_by(self.orderAscDbClassReverse(ContractLocation.lfn))

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

    args = parser.parse_args()

    app.run(host=args.interface, port=args.port)
