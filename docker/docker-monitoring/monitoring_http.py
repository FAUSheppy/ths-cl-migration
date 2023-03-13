#!/usr/bin/python3

import argparse
import requests
import os
import datetime
import config

if __name__ == "__main__":

    url               = config.URL
    monitoring_server = config.MONITORING_SERVER
    monitoring_token  = config.MONITORING_TOKEN
    service_name      = config.SERVICE_NAME
    project_id        = config.PROJECT_ID or 0
    timeout           = config.MONITORING_TIMEOUT or 10

    main      = requests.get("{}/".format(url), timeout=args.timeout)
    entry     = requests.get("{}/entry-content?projectId={}".format(url, args.project_id), timeout=args.timeout)
    documents = requests.get("{}/new-document?projectId={}".format(url, args.project_id), timeout=args.timeout)
    downloadFormat = "{}/new-document?projectId={}&template=BD_Leckortung.docx"
    documentDownload = requests.head(downloadFormat.format(url, args.project_id), timeout=args.timeout)
    
    error = ""
    try:
        main.raise_for_status()
    except requests.HTTPError as e:
        error += "Error: Main Page - {}\n".format(e.response.status_code)

    try:
        entry.raise_for_status()
    except requests.HTTPError as e:
        error += "Error: Entry Info Page - {}\n".format(e.response.status_code)

    try:
        documents.raise_for_status()
    except requests.HTTPError as e:
        error += "Error: Documents Page - {}\n".format(e.response.status_code)

    try:
        documentDownload.raise_for_status()
    except requests.HTTPError as e:
        error += "Error: Document Download - {}\n".format(e.response.status_code)

    r = requests.post(monitoring_server, 
                        json={"service" : service_name,
                              "token" : monitoring_token,
                              "status" : status,
                              "info" : "\n" + error.strip("\n")})

    r.raise_for_status()
