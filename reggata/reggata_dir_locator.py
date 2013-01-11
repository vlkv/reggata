import sys
import os

# Solution is taken from here: 
# http://stackoverflow.com/questions/2632199/how-do-i-get-the-path-of-the-current-executed-file-in-python
def weAreFrozen():
    # All of the modules are built-in to the interpreter, e.g., by py2exe
    return hasattr(sys, "frozen")

def modulePath():
    if weAreFrozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(__file__)
