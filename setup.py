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

class UnsupportedPlatform(Exception):
    pass

class VersionInfoNotFound(Exception):
    pass 


def get_reggata_version():
    f = open("version.txt", "r")
    version = f.readline()
    if not version or len(version) == 0:
        raise VersionInfoNotFound()
    f.close()
    return version.strip()


def get_short_sys_platform():
    if sys.platform.startswith("linux"):
        return "linux"
    elif sys.platform.startswith("win"):
        return "win"
    elif sys.platform.startswith("darwin"):
        return "mac"
    else:
        raise UnsupportedPlatform()
    

if __name__ == '__main__':
    
    sys.path.append(r'.' + os.sep + 'ui')
    sys.path.append(r'.' + os.sep + 'lib')
    sys.path.append(r'.' + os.sep + 'src')
    
    base = None
    if sys.platform.startswith("win"):
        base = "Win32GUI"
    
    reggata_version = get_reggata_version()
    target_dir = os.path.join("bin", "reggata-" + reggata_version + "_" + get_short_sys_platform()) 
    buildOptions = dict(
            compressed = True,
            includes = ["sqlite3"],
            packages = ["sqlalchemy.dialects.sqlite", "ply"],
            namespace_packages=["sqlalchemy"],
            include_files = ["reggata_ru.qm", "COPYING", "README.creole", 
                             "version.txt", "reggata.conf.template"],
            build_exe = target_dir
            )
    setup(
            name = "Reggata",
            version = reggata_version,
            description = "Reggata is a tag-based file manager",
            options = dict(build_exe = buildOptions),
            executables = [Executable('.' + os.sep + 'src' + os.sep + 'reggata.py', base = base)]
            )
    
    if sys.platform.startswith("win"):
        file, PyQt4_path, desc = imp.find_module("PyQt4")
        shutil.copytree(PyQt4_path + os.sep + "plugins" + os.sep + "imageformats", target_dir + os.sep + "imageformats")
    
    print("Done")

