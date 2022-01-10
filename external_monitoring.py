#!/usr/bin/python3

import argparse
import requests
import os
import datetime

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='THS Contract Locations Monitoring Script')
    parser.add_argument('--url', default="localhost", help='Interface to target for check')

    parser.add_argument('--monitoring-server', help='Monitoring Server')
    parser.add_argument('--monitoring-token', help='Token for Monitoring Server')
    parser.add_argument('--service-name', help='Service Name to submit as')
    
    parser.add_argument('--project-id', help='A existing project-id to check')
    parser.add_argument('--timeout', type=int, default=10, help='Timeout for individual requests in seconds.')

    parser.add_argument('--check-for-backup-file', help='Check for a backup confirmation file here.')

    args = parser.parse_args()

    main      = requests.get("{}/".format(args.url), timeout=args.timeout)
    entry     = requests.get("{}/entry-content?projectId={}".format(args.url, args.project_id), timeout=args.timeout)
    documents = requests.get("{}/new-document?projectId={}".format(args.url, args.project_id), timeout=args.timeout)
    downloadFormat = "{}/new-document?projectId={}&template=BD_Leckortung.docx"
    documentDownload = requests.head(downloadFormat.format(args.url, args.project_id), timeout=args.timeout)
    
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


    if args.check_for_backup_file:
        filename = args.check_for_backup_file
        if not os.path.isfile(filename):
            errro += "Missing Backup Info File {}".format(filename)
        else:
            with open(filename, "r") as f:
                content = f.read()
                try:
                    lastBackup = datetime.datetime.strptime(content, "%y_%m_%d_%H_%M")
                    if datetime.datetime.now() - lastBackup > datetime.timedelta(days=2):
                        error += "Local Backup found but was at {}".format(content)
                except ValueError:
                    error += "Local Backup info file has malformed content: {}".format(content)

    status = "UNKNOWN"
    if error:
        status = "CRITICAL"
    else:
        status = "OK"

    r = requests.post(args.monitoring_server, 
                        json={"service" : args.service_name,
                              "token" : args.monitoring_token,
                              "status" : status,
                              "info" : "\n" + error.strip("\n")})
    r.raise_for_status()