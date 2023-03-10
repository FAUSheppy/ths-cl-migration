#!/usr/bin/python3

import argparse
import stat
import glob
import time

from sqlalchemy import Column, Integer, String, Boolean, or_, and_
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func
import sqlalchemy
from sqlalchemy import Column, Integer, String, Boolean, or_, and_
from sqlalchemy.orm import declarative_base
import os
import config

import datetime
import json

STATUS_FILE = "import_status.json"

base   = declarative_base()
engine = None
sm =  None

class ProjectPath(base):
    __tablename__ = "project_paths"
    projectid       = Column(Integer, primary_key=True)
    projectpath     = Column(String)

def isProjectDir(filename):
    basedir = os.path.basename(filename)
    return os.path.isdir(filename) and basedir.startswith("P-")

def pidFromPath(filename):

    basename = os.path.basename(filename)
    idWithDashList = basename.split("P-")
    if len(idWithDashList) != 2:
        return None
    idWithDash = idWithDashList[1]
    pid = idWithDash.replace("-", "")
    return int(pid)

def load(root, removePrefix=""):

    session = sm()
    for filename in glob.iglob(root + '**/*', recursive=True):
        
        if isProjectDir(filename):
            clean = filename[len(removePrefix):]
            pid = pidFromPath(filename)
            print(pid, clean)
            pp = ProjectPath(projectid=pid, projectpath=clean)
            session.merge(pp)
            session.commit()
        
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Start THS-Contract Locations')

    parser.add_argument('--engine',
        help="Engine connection string, e.g. postgresql+psycopg2://user:pass@localhost/ths")
    parser.add_argument('--base-path', type=str, help='Base path to search in')
    parser.add_argument('--start', type=int, default=2008, help='Year to start in')
    parser.add_argument('--end',   type=int, default=2023, help='Year to end in')
    args = parser.parse_args()

    engine = args.engine
    if not engine:
        import config
        engine = config.SQLALCHEMY_DATABASE_URI

    base_path = args.base_path
    if not base_path:
        import config
        base_path = config.FILESYSTEM_PROJECTS_BASE_PATH

    engine = sqlalchemy.create_engine(engine)
    sm = sessionmaker(bind=engine)
    
    base.metadata.create_all(engine)
   
    paths = [ "{}/Jahr {}/".format(base_path, x)
                    for x in range(args.start, args.end + 1)]

    status = dict()
    if os.path.isfile(STATUS_FILE):
        with open(STATUS_FILE) as f:
            status = json.load(f)

    for yearPath in paths:

        if yearPath in status:
            t = datetime.datetime.fromisoformat(status[yearPath])
            if t - datetime.datetime.now() < datetime.timedelta(days=7):
                continue
            
        print("Loading:", yearPath)
        load(yearPath, base_path + "/")
        status.update({ yearPath : datetime.datetime.now().isoformat() })

    with open(STATUS_FILE, "w") as f:
        f.write(json.dumps(status, indent=2))
