# -*- coding: utf-8 -*-
'''
Created on 04.10.2010
@author: vlkv

Module contains various constants.
'''
import os
from user_config import UserConfig
import ply.yacc
import ply.lex

DEBUG = False

ROOT_LOGGER = "reggata"

METADATA_DIR = ".reggata"
DB_FILE = "database.sqlite3"
USER_CONFIG_DIR = os.path.expanduser("~") + os.sep + ".config" + os.sep + "reggata"
USER_CONFIG_FILE = USER_CONFIG_DIR + os.sep + "reggata.conf"
LOGGING_CONFIG_FILE = USER_CONFIG_DIR + os.sep + "logging.conf"

THUMBNAIL_DEFAULT_SIZE = 100

DEFAULT_TMP_DIR = USER_CONFIG_DIR + os.sep + "tmp"

RATING_FIELD = UserConfig().get("reserved_fields.rating", "Rating")
NOTES_FIELD = UserConfig().get("reserved_fields.notes", "Notes")
RESERVED_FIELDS = [RATING_FIELD, NOTES_FIELD]

#Some custom logger (from logging module) can be substituted here
yacc_errorlog = ply.yacc.NullLogger()
lex_errorlog = ply.lex.NullLogger()

STATUSBAR_TIMEOUT = 5000

DEFAULT_USER_LOGIN = "user"
DEFAULT_USER_PASSWORD = ""