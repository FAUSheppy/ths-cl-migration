#!/usr/bin/env python3
import sys
import os
import subprocess
import urllib.parse

WORD_PATH="C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.exe"
PDF="C:\\Program Files\\Adobe\\Acrobat DC\\Acrobat\\Acrobat.exe"
PICTURE="C:\\Program Files\\IrfanView\\i_view64.exe"

if __name__ == "__main__":
    
    script   = sys.argv[0]
    print(sys.argv[1])
    splitter = "?"
    if "/?" in sys.argv[1]:
        splitter = "/?"

    file, id = urllib.parse.unquote(sys.argv[1]).split(splitter)
    print(file)
    file = file.lstrip("localfile://")

    if file[1] != ":":
        file = file[0] + ":" + file[1:]

    app    = ""
    auth = ""
    with open(os.path.join(os.path.dirname(script), "id.txt")) as f:
        auth = f.read().strip()

    if not auth == id:
        input("Auth Missmatch")
        sys.exit(1)
    elif file.endswith(".docx"):
        app = WORD_PATH
    elif file.lower().endswith(".jpg"):
        app = PICTURE
    elif file.lower().endswith("pdf"):
        app = PDF
    else:
        input("Bad Datatype")
        sys.exit(1)

    cmd = [app, file]
    print(cmd)
    subprocess.Popen(cmd)
    sys.exit(0)