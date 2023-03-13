#!/usr/bin/python3

import argparse
import requests
import os
import datetime
import config
import time

if __name__ == "__main__":

    while(True):

        url               = config.URL
        monitoring_server = config.MONITORING_SERVER
        monitoring_token  = config.MONITORING_TOKEN
        service_name      = config.SERVICE_NAME
        project_id        = config.PROJECT_ID or 0
        timeout           = config.MONITORING_TIMEOUT or 10

        main      = requests.get("{}/".format(url), timeout=timeout)
        entry     = requests.get("{}/entry-content?projectId={}".format(url, project_id), timeout=timeout)
        documents = requests.get("{}/new-document?projectId={}".format(url, project_id), timeout=timeout)
        downloadFormat = "{}/new-document?projectId={}&template=BD_Leckortung.docx"
        documentDownload = requests.head(downloadFormat.format(url, project_id), timeout=timeout)
        
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

        status = "UNKNOWN"
        if error:
            status = "CRITICAL"
        else:
            status = "OK"

        r = requests.post(monitoring_server, 
                            json={"service" : service_name,
                                  "token" : monitoring_token,
                                  "status" : status,
                                  "info" : "\n" + error.strip("\n")})

        r.raise_for_status()

        time.sleep(5*60)
