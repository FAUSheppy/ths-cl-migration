import os
import zipfile
import argparse
import sys
import glob
import shutil

def getFixedBitstream(path, oldIP, oldPort, newIP, newPort):

    tmpDir = "/tmp/doc-connection-build/"

    # remove old working dir #
    if os.path.isdir(tmpDir):
        shutil.rmtree(tmpDir)

    # recreate dir
    os.mkdir(tmpDir)

    # copy file to tmp path #
    fullTempPath = os.path.join(tmpDir, os.path.basename(path))
    shutil.copy2(path, fullTempPath)

    # unpack docx-d is outdir and -o is overwrite
    with zipfile.ZipFile(fullTempPath, 'r') as zf:
        zf.extractall(tmpDir)

    # edit xml (add active record + query) #
    xmlPath = os.path.join(tmpDir, "word/settings.xml")
    
    fileContentTmp = None
    with open(xmlPath, 'r') as f:
        fileContentTmp = f.read()

    #with open("debug_pre.xml", "w") as f:
    #    f.write(fileContentTmp)

    if oldIP in fileContentTmp and oldPort in fileContentTmp:
        print("Found in  {}".format(path))
    else:
        print("Doing nothing")
        return None

    fileContentTmp = fileContentTmp.replace(oldIP, newIP)
    fileContentTmp = fileContentTmp.replace(oldPort, newPort)
    
    #with open("debug_post.xml", "w") as f:
    #    f.write(fileContentTmp)

    with open(xmlPath, 'w') as f:
        f.write(fileContentTmp)

    # remove old result file
    os.remove(fullTempPath)

    # repack into new docx
    shutil.make_archive("../" + fullTempPath, 'zip', root_dir=tmpDir, base_dir=".")
    os.rename("../" + fullTempPath + ".zip", fullTempPath)
   
    # transform new file into bitstream
    content = None
    with open(fullTempPath, "rb") as f:
        content = f.read()

    shutil.rmtree(tmpDir)

    print("rewriting this file")
    with open(path, "wb") as f:
        f.write(content)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Start THS-Contract Locations')

    parser.add_argument('--base-path', required=True, type=str, help='Base path to search in')
    parser.add_argument('--start', type=int, default=2020, help='Year to start in')
    parser.add_argument('--end',   type=int, default=2023, help='Year to end in')
    args = parser.parse_args()

    paths = [ "{}/Jahr {}/".format(args.base_path, x)
                    for x in range(args.start, args.end + 1)]

    oldIP = "192.168.178.67"
    newIP = "192.168.178.80"
    oldPort = "5432"
    newPort = "5433"

    print(oldIP, oldPort, newIP, newPort, sep="\n")
    print("\n".join(paths))

    for yearPath in paths:
        
        for filename in glob.iglob(yearPath + '**/*', recursive=True):
            basename = os.path.basename(filename)
            if(os.path.isfile(filename)
                        and filename.endswith(".docx")
                        and not basename.startswith(".")
                        and not basename.startswith("~")):
                bst = getFixedBitstream(filename, oldIP=oldIP, oldPort=oldPort,
                                            newIP=newIP, newPort=newPort)
