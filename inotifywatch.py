import inotify.adapters
from inotify.constants import *
from config import FILESYSTEM_PROJECTS_BASE_PATH

import argparse
import os
import stat

from sqlalchemy import Column, Integer, String, Boolean, or_, and_
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func
import sqlalchemy
from sqlalchemy import Column, Integer, String, Boolean, or_, and_
from sqlalchemy.orm import declarative_base

base   = declarative_base()
engine = None
sm =  None

class ProjectDirectory(base):

    __tablename__ = "project_paths"

    projectId     = Column(String, primary_key=True)
    projectDir    = Column(String)
    fullpath      = Column(String)

def save(projectId, fullpath, projectDir):

    projectDirectory = ProjectDirectory(dirname=projectDir, projectId=str(projectId),
                                        fullpath=fullpath)
    session = sm()
    session.merge(projectDirectory)
    session.commit()

def inotifyRun():

    inotifyMask = (IN_MOVE | IN_CREATE | IN_DELETE | IN_DELETE_SELF | IN_ONLYDIR | IN_ISDIR)
    inotifyMask = IN_ALL_EVENTS
    i = inotify.adapters.InotifyTree(FILESYSTEM_PROJECTS_BASE_PATH, mask=inotifyMask)

    for event in i.event_gen(yield_nones=False):

        # split event
        _, type_names, path, filename = event

        fullpath = os.path.join(path, filename)
        if not os.path.isdir(fullpath):
            continue

        print("PATH=[{}] FILENAME=[{}] EVENT_TYPES={}".format(path, filename, type_names))

        projectId = None
        if "P-" in filename:
            p, part1, part2 = filename.split("-")
            projectId = int("{}{}".format(part1, part2))
            save(projectId, path, filename)
        else:
            continue

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Project Filesystem listener')

    parser.add_argument('ENGINE',
        help="Engine connection string, e.g. postgresql+psycopg2://user:pass@localhost/ths")
    args = parser.parse_args()

    engine = sqlalchemy.create_engine(args.ENGINE)
    sm = sessionmaker(bind=engine)
    base.metadata.create_all(engine)

    inotifyRun()
