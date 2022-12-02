def buildPath(contractLocation, flaskApp):

    base = flaskApp.config["FILESYSTEM_RPOEJECTS_BASE_PATH"]
    year = contractLocation.getProjectYear()
    path = os.path.join(base, "Jahr {}".format(year))
    pathWithName = os.path.join(path, contractLocation.nachname.strip())

    returnPath = None
    if os.path.isdir(pathWithName):
        returnPath = pathWithName
    else:
        returnPath = path # the year path

    return (pathToReturn, cl.getProjectDir(), year)


