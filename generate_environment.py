import sys

if __name__ == "__main__":

    try:
        import config
    except ModuleNotFoundError:
        print("Missing config.py configuration, see README.md for more information")
        sys.exit(1)
    
    try:
        fspath = config.FILESYSTEM_PROJECTS_BASE_PATH
        cppath = config.CLIENT_PATH_PREFIX
        skey   = config.SECRET_KEY
        pgdata = config.PG_DATA_LOCATION
        tpdir  = config.TEMPLATES_DIR
        cfile  = config.CONFIG_FILE
        bwfile = config.BWA_FILE
        pgport = config.PG_OUTSIDE_PORT
        pguser = config.PG_USER
        pgdb   = config.PG_DB
        pgpass = config.PG_PASS
        pghost = config.PG_HOST
    except AttributeError as e:
        print("Missing {}".format(str(e).split(" ")[-1]))
        sys.exit(1)
        
    outkeys = list(filter(lambda x: not x.startswith("_"), config.__dict__.keys()))
    outdict = dict()

    for key in outkeys:
        outdict.update({key : config.__dict__[key]})

    engineFmtString = "postgresql+psycopg2://{user}:{password}@{host}:5432/{db}"
    outdict.update({ "SQLALCHEMY_DATABASE_URI" : engineFmtString.format(user=config.PG_USER,
                                password=config.PG_PASS, db=config.PG_DB, host=config.PG_HOST) })

    DOCKER_ENV_FILES = [ "./docker/docker-compose-main/.env" ]

    for fname in DOCKER_ENV_FILES:
        with open(fname, "w") as f:
            for key, value in outdict.items():

                if type(value) == bool:
                    continue
                if type(value) == str:
                    value = value.replace("\\", "\\\\") # escape backslash
                    value = value.replace(" ", "\\ ") # escape space

                fmtString = '{}={}\n'
                f.write(fmtString.format(key, value))
