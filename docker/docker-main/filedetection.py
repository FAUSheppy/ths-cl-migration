import os

def detectType(fullpath):
    if os.path.isfile(fullpath):
        return "file_not_found_contact_admin"
    return "unkown" 
    
