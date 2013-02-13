'''
Created on 04.10.2010
@author: vlkv

Module contains various global constants.
'''
import os

DEBUG = False

ROOT_LOGGER = "reggata"

METADATA_DIR = ".reggata"
DB_FILE = "database.sqlite3"
USER_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "reggata")
USER_CONFIG_FILE = os.path.join(USER_CONFIG_DIR, "reggata.conf")
LOGGING_CONFIG_FILE = os.path.join(USER_CONFIG_DIR, "logging.conf")

THUMBNAIL_DEFAULT_SIZE = 100

DEFAULT_TMP_DIR = USER_CONFIG_DIR + os.sep + "tmp"

RATING_FIELD = "Rating"
NOTES_FIELD = "Notes"
RESERVED_FIELDS = [RATING_FIELD, NOTES_FIELD]

STATUSBAR_TIMEOUT = 5000

DEFAULT_USER_LOGIN = "user"
DEFAULT_USER_PASSWORD = ""


MAX_FILE_SIZE_FOR_FULL_HASHING = 100*1024*1024
MAX_BYTES_FOR_PARTIAL_HASHING = 10*1024*1024
