# This is a config file for building with cx_freeze binary Reggata distribution

import sys
from cx_Freeze import setup, Executable
import imp
import os
import shutil

class UnsupportedPlatform(Exception):
    pass


class VersionInfoNotFound(Exception):
    pass


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

    sys.path.append(os.path.join("..", "locale"))
    sys.path.append(os.path.join("..", "reggata"))

    base = None
    targetExeName = "reggata"
    if sys.platform.startswith("win"):
        base = "Win32GUI"
        targetExeName = targetExeName + ".exe"

    import reggata
    reggata_version = reggata.__version__
    print("Reggata version is " + reggata_version)
    target_dir = os.path.join(
        "..", "binary_builds", "reggata-" + reggata_version + "_" + get_short_sys_platform())
    buildOptions = dict(
            compressed = True,
            includes = ["sqlite3"],
            packages = ["sqlalchemy.dialects.sqlite", "ply"],
            include_files = [("../reggata/locale/reggata_ru.qm", "locale/reggata_ru.qm"),
                             ("../COPYING", "COPYING"),
                             ("../README.creole", "README.creole"),
                             ("../git_version.txt", "git_version.txt"),
                             ("../bin/reggata.sh", "reggata.sh"),
                             ],
            build_exe = target_dir
    )
    setup(
            name = "Reggata",
            version = reggata_version,
            description = "Reggata is a tag-based file manager",
            options = dict(build_exe = buildOptions),
            executables = [Executable(os.path.join('..', 'reggata', 'main.py'),
                                      base = base,
                                      targetName = targetExeName)]
    )

    if sys.platform.startswith("win"):
        file, PyQt4_path, desc = imp.find_module("PyQt4")
        shutil.copytree(os.path.join(PyQt4_path, "plugins", "imageformats"),
                        os.path.join(target_dir, "imageformats"))
    elif sys.platform.startswith("linux"):
        # TODO: automate search for these libraries:
        shutil.copy("/usr/lib/qt4/libQtCore.so.4", os.path.join(target_dir, "libQtCore.so.4"))
        shutil.copy("/usr/lib/qt4/libQtGui.so.4", os.path.join(target_dir, "libQtGui.so.4"))
    print("Done.")

