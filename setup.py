#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup
import reggata


def read_file(filename):
    """Returns the text of the given filename."""
    with open(filename, "r") as f:
        text = f.read()
    return text


setup(
    name = "reggata",
    packages = ['reggata', 
                'reggata.data',
                'reggata.gui',
                'reggata.logic',
                'reggata.parsers',
                'reggata.tests'],
    package_dir={'reggata': 'reggata',
                 'reggata.data': 'reggata/data',
                 'reggata.gui': 'reggata/gui',
                 'reggata.logic': 'reggata/logic',
                 'reggata.parsers': 'reggata/parsers',
                 'reggata.tests': 'reggata/tests'},
    scripts = ["reggata/reggata"],
    version = reggata.__version__,
    description = reggata.__doc__,
    author = reggata.__author__,
    author_email = reggata.__author_email__,
    license = reggata.__license__,
    url = reggata.__url__,
    download_url = reggata.__download_url__,
    keywords = ["tags", "tagging", "documents", "files"],
    classifiers = [
        "Programming Language :: Python",
        "License :: OSI Approved :: BSD License",
        "Operating System :: MacOS",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Natural Language :: English",
        "Intended Audience :: Developers",
        "Topic :: Office/Business",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development"
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities"],
    long_description = read_file("./README.creole")
)
