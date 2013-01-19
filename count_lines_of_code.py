# Prints recursive count of lines of python source code from <current dir>/src

import os
startPath = os.path.join(os.getcwd(), "reggata")
ignore_set = set(["__init__.py", "resources_rc.py"])

resultsList = []
for pydir, _, pyfiles in os.walk(startPath):
    for pyfile in pyfiles:
        if not pyfile.endswith(".py"):
            continue
        if pyfile in ignore_set or pyfile.startswith("ui_"):
            continue
        absPath = os.path.join(pydir, pyfile)
        
        linesCount = len(open(absPath, "r").read().splitlines())
        filename = os.path.relpath(absPath, startPath)
        
        resultsList.append((linesCount, filename))

for linesCount, filename in resultsList: 
    print("%d lines in %s" % (linesCount, filename))

print("\nTotal: %s lines (%s)" %(sum([x[0] for x in resultsList]), startPath))
