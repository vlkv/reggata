# -*- coding: utf-8 -*-
'''
Created on 04.10.2010

@author: vlkv

Модуль содержит различные константы.
'''
import os

METADATA_DIR = ".reggata"
DB_FILE = "database.sqlite3"
INIT_DB_SQL = "init_db.sql"

USER_CONFIG_DIR = os.path.expanduser("~") + os.sep + ".config" + os.sep + "reggata"
REGGATA_INI = "reggata.ini"
USER_CONFIG_FILE = USER_CONFIG_DIR + os.sep + REGGATA_INI

