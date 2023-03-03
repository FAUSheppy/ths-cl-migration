#!/usr/bin/python3

import argparse
import stat
import glob

from sqlalchemy import Column, Integer, String, Boolean, or_, and_
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func
import sqlalchemy
from sqlalchemy import Column, Integer, String, Boolean, or_, and_
from sqlalchemy.orm import declarative_base
import os

base   = declarative_base()
engine = None
sm =  None

class ProjectPath(base):
    __tablename__ = "project_paths"
    projectid       = Column(String, primary_key=True)
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
    return pid

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

    parser.add_argument('ENGINE',
        help="Engine connection string, e.g. postgresql+psycopg2://user:pass@localhost/ths")
    parser.add_argument('BASE_PATH', type=str, help='Base path to search in')
    parser.add_argument('--start', type=int, default=2008, help='Year to start in')
    parser.add_argument('--end',   type=int, default=2023, help='Year to end in')


    args = parser.parse_args()
    engine = sqlalchemy.create_engine(args.ENGINE)
    sm = sessionmaker(bind=engine)
    
    base.metadata.create_all(engine)
   
    paths = [ "{}/THS_Proj/Jahr {}/".format(args.BASE_PATH, x)
                    for x in range(args.start, args.end + 1)]

    for yearPath in paths:
        print("Loading:", yearPath)
        load(yearPath, args.BASE_PATH + "/")
