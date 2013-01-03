# -*- coding: utf-8 -*-

from setuptools import setup
#from distutils.core import setup
import reggata


def read_file(filename):
    """Returns the text of the given filename."""
    with open(filename, "r") as f:
        text = f.read()
    return text


setup(
    name = "Reggata",
    packages = ['reggata', 
                'reggata.data',
                'reggata.gui',
                'reggata.ui',
                'reggata.logic',
                'reggata.parsers',
                'reggata.tests'],
    package_dir={'reggata': 'reggata',
                 'reggata.data': 'reggata/data',
                 'reggata.gui': 'reggata/gui',
                 'reggata.ui': 'reggata/ui',
                 'reggata.logic': 'reggata/logic',
                 'reggata.parsers': 'reggata/parsers',
                 'reggata.tests': 'reggata/tests'},
    scripts = ["bin/reggata"],
    version = reggata.__version__,
    description = reggata.__doc__,
    author = reggata.__author__,
    author_email = reggata.__author_email__,
    license = reggata.__license__,
    url = reggata.__url__,
    download_url = reggata.__download_url__,
    keywords = ["tags", "tagging", "documents", "files"],
    long_description = read_file("./README.creole"),
    install_requires=[
        'ply',
        'SQLAlchemy'
        # NOTE: Reggata also needs PyQt4, it must be installed manually
    ]
)
