import inotify.adapters
from inotify.constants import *
import config
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

    __tablename__ = "project_paths_fs"

    projectid     = Column(Integer, primary_key=True)
    projectpath   = Column(String)

def save(projectId, fullpath, projectDir):

    projectDirectory = ProjectDirectory(projectid=str(projectId),
                                        projectpath=fullpath)
    session = sm()
    session.merge(projectDirectory)
    session.commit()

def inotifyRun(project_path):

    inotifyMask = (IN_MOVE | IN_CREATE | IN_DELETE | IN_DELETE_SELF | IN_ONLYDIR )
    inotifyMask = IN_ALL_EVENTS

    if not project_path:
        project_path = "/app/proj/" # docker path

    i = inotify.adapters.InotifyTree(project_path, mask=inotifyMask)

    for event in i.event_gen(yield_nones=False):

        # split event
        _, type_names, path, filename = event

        if any([ s in [ "IN_CLOSE_NOWRITE", "IN_ACCESS", "IN_OPEN" ] for s in type_names]):
            continue

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

    parser.add_argument('--engine',
        help="Engine connection string, e.g. postgresql+psycopg2://user:pass@localhost/ths")
    parser.add_argument('--project-path', help="Project path for Contract struct")
    args = parser.parse_args()

    engine_string = args.engine
    if not engine_string:
        engine_string = config.SQLALCHEMY_DATABASE_URI

    print(engine_string)
    engine = sqlalchemy.create_engine(engine_string)
    sm = sessionmaker(bind=engine)
    base.metadata.create_all(engine)

    inotifyRun(args.project_path)
