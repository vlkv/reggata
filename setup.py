# A simple setup script to create an executable using PyQt4. This also
# demonstrates the method for creating a Windows executable that does not have
# an associated console.
#
# PyQt4app.py is a very simple type of PyQt4 application
#
# Run the build process by running the command 'python setup.py build'
#
# If everything works well you should find a subdirectory in the build
# subdirectory that contains the files needed to run the application

import sys

from cx_Freeze import setup, Executable


sys.path.append(r'.\ui')
sys.path.append(r'.\lib')
sys.path.append(r'.\src')
sys.path.append(r'c:\usr\Python31_2\lib\sqlite3')

print("sys.path={}".format(sys.path))

base = "Console"

buildOptions = dict(
        compressed = True,
        includes = ["sqlite3"],
        packages = ["sqlalchemy.dialects.sqlite", "ply"],
        #namespacePackages=["sqlalchemy"]
        )
    

setup(      
        name = "Reggata",
        version = "0.1",
        description = "Reggata is a tag-based file manager",    
        options = dict(build_exe = buildOptions),
        executables = [Executable(".\src\main_window.py", base = base)])

