# To build executable package with cx_freeze just execute command:
#   python setup.py build
#
# Command to upload release
# scp [archive.tar.gz] vlkv,reggata@frs.sourceforge.net:/home/frs/project/r/re/reggata/[version]

import sys

from cx_Freeze import setup, Executable
import imp
import os
import shutil

target_dir = "bin" + os.sep + "build"

sys.path.append(r'.' + os.sep + 'ui')
sys.path.append(r'.' + os.sep + 'lib')
sys.path.append(r'.' + os.sep + 'src')


#base = "Console"
base = None
if sys.platform == "win32":
    base = "Win32GUI"

f = open("version.txt", "r")
reggata_version = f.readline()
f.close()

buildOptions = dict(
        compressed = True,
        includes = ["sqlite3"],
        packages = ["sqlalchemy.dialects.sqlite", "ply"],
        namespace_packages=["sqlalchemy"],
	include_files = ["reggata_ru.qm", "COPYING", "README.creole", "version.txt", "reggata.conf.template"],
	#zip_includes = ["version.txt"],
        build_exe = target_dir
        )
setup(
        name = "Reggata",
	
	#TODO create some script to automate version generation...
        version = reggata_version,
        description = "Reggata is a tag-based file manager",
        options = dict(build_exe = buildOptions),
        executables = [Executable('.' + os.sep + 'src' + os.sep + 'main_window.py', base = base)])

if sys.platform == "win32":
    file, PyQt4_path, desc = imp.find_module("PyQt4")
    shutil.copytree(PyQt4_path + os.sep + "plugins" + os.sep + "imageformats", target_dir + os.sep + "imageformats")

print("Done")
