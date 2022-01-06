#!/usr/bin/python3

import argparse
import requests

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='THS Contract Locations Monitoring Script')
    parser.add_argument('--url', default="localhost", help='Interface to target for check')

    parser.add_argument('--monitoring-server', help='Monitoring Server')
    parser.add_argument('--monitoring-token', help='Token for Monitoring Server')
    parser.add_argument('--service-name', help='Service Name to submit as')
    
    parser.add_argument('--project-id', help='A existing project-id to check')
    parser.add_argument('--timeout', type=int, default=5, help='Timeout for individual requests in seconds.')

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