#!/usr/bin/python3

from smbprotocol.connection import Connection, Dialects
import smbprotocol.exceptions
import smbclient
import argparse
import stat

from sqlalchemy import Column, Integer, String, Boolean, or_, and_
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func
import sqlalchemy
from sqlalchemy import Column, Integer, String, Boolean, or_, and_
from sqlalchemy.orm import declarative_base

base   = declarative_base()
engine = sqlalchemy.create_engine('sqlite:///database.sqlite')
sm = sessionmaker(bind=engine)

class ProjectPathsByDir(base):
    __tablename__ = "project_paths"
    dirname       = Column(String, primary_key=True)
    fullpath      = Column(String)

pDirPathMap = dict()
isdir = lambda path: stat.S_ISDIR(smbclient.lstat(path).st_mode)

def isProjectDir(string):
    return string.startswith("P-")

def sambaRecurse(dirPath):

    listing = smbclient.listdir(dirPath)
    dirsToRecurse = []

    # check content #
    print(dirPath)
    for el in listing:
        cur = dirPath + "/" + el
        if isdir(cur):
            print(cur)
            if isProjectDir(el):
                # pDirPathMap.update({ el  : cur })
                session = sm()
                session.merge(ProjectPathsByDir(dirname=el, fullpath=cur))
                session.commit()
                print(el, cur)
            else:
                dirsToRecurse.append(cur)
        else:
            continue

    # work through recursion map #
    for recDir in dirsToRecurse:
        sambaRecurse(recDir)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Start THS-Contract Locations')

    parser.add_argument('--smbserver', required=True, help='SMB Server Target')
    parser.add_argument('--smbuser',   required=True, help='SMB User')
    parser.add_argument('--smbpass',   required=True, help='SMB Password')
    parser.add_argument('--smbshare',  required=True, default="THS", help='SMB Password')

    parser.add_argument('--start', type=int, default=2008, help='Year to start in')
    parser.add_argument('--end',   type=int, default=2021, help='Year to end in')

    args = parser.parse_args()
    
    base.metadata.create_all(engine)
    
    smbclient.register_session(args.smbserver, username=args.smbuser, password=args.smbpass)
    
    for yearPath in [ "THS_Proj/Jahr " + str(x) for x in range(args.start, args.end + 1)]:
        print(yearPath)
        base =  "\\\\{}\{}\\{}".format(args.smbserver, args.smbshare, yearPath)
        sambaRecurse(base)
