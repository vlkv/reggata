# To build executable package with cx_freeze just execute command:
#   python setup.py build

import sys

from cx_Freeze import setup, Executable
import imp
import os
import shutil

target_dir = "bin" + os.sep + "build"

sys.path.append(r'.' + os.sep + 'ui')
sys.path.append(r'.' + os.sep + 'lib')
sys.path.append(r'.' + os.sep + 'src')

base = "Console"

buildOptions = dict(
        compressed = True,
        includes = ["sqlite3"],
        packages = ["sqlalchemy.dialects.sqlite", "ply"],
        namespace_packages=["sqlalchemy"],
	include_files = ["reggata_ru.qm"],
        build_exe = target_dir
        )
setup(
        name = "Reggata",
        version = "0.1_beta2",
        description = "Reggata is a tag-based file manager",
        options = dict(build_exe = buildOptions),
        executables = [Executable('.' + os.sep + 'src' + os.sep + 'main_window.py', base = base)])

if sys.platform == "win32":
    file, PyQt4_path, desc = imp.find_module("PyQt4")
    shutil.copytree(PyQt4_path + os.sep + "plugins" + os.sep + "imageformats", target_dir + os.sep + "imageformats")

print("Done")
