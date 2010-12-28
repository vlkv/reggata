# To build executable with cx_freeze just execute command:
#   python setup.py build

import sys

from cx_Freeze import setup, Executable
import imp
import os
import shutil

target_dir = "cx_freezed"

sys.path.append(r'.' + os.sep + 'ui')
sys.path.append(r'.' + os.sep + 'lib')
sys.path.append(r'.' + os.sep + 'src')
#sys.path.append(r'c:\usr\Python31_2\lib\sqlite3')

base = "Console"

buildOptions = dict(
        compressed = True,
        includes = ["sqlite3"],
        packages = ["sqlalchemy.dialects.sqlite", "ply"],
        namespace_packages=["sqlalchemy"],
        build_exe = target_dir
        )
setup(      
        name = "Reggata",
        version = "0.1",
        description = "Reggata is a tag-based file manager",    
        options = dict(build_exe = buildOptions),
        executables = [Executable('.' + os.sep + 'src' + os.sep + 'main_window.py', base = base)])

file, PyQt4_path, desc = imp.find_module("PyQt4")
shutil.copytree(PyQt4_path + os.sep + "plugins" + os.sep + "imageformats", target_dir + os.sep + "imageformats")

print("Done")
