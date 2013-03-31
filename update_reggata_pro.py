#!/usr/bin/python3

import os
startPath = os.path.join(os.getcwd(), "reggata")

ignoreRelPaths = ["reggata/ui/resources_rc.py"]

forms = []
sources = []
for pydir, _, pyfiles in os.walk(startPath):
    for pyfile in pyfiles:
        absPath = os.path.join(pydir, pyfile)
        relPath = os.path.relpath(absPath, os.getcwd())
        
        if relPath in ignoreRelPaths:
            continue
        
        if pyfile.endswith(".py"):
            sources.append(relPath)

        elif pyfile.endswith(".ui"):
            forms.append(relPath)
            
with open("reggata.pro", "w") as f:
    if len(forms) > 0:
        f.write("FORMS += \\" + os.linesep)
    for form in forms:
        f.write("\t" + form + " \\" + os.linesep)
    f.write(os.linesep)
    
    if len(sources) > 0:
        f.write("SOURCES += \\" + os.linesep)
    for src in sources:
        f.write("\t" + src + " \\" + os.linesep)
    f.write(os.linesep)
        

    f.write("TRANSLATIONS += reggata_ru.ts" + os.linesep)
    
