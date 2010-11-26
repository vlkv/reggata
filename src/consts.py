# -*- coding: utf-8 -*-
'''
Copyright 2010 Vitaly Volkov

This file is part of Reggata.

Reggata is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Reggata is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Reggata.  If not, see <http://www.gnu.org/licenses/>.


Created on 04.10.2010

@author: vlkv

Модуль содержит различные константы.
'''
import os

METADATA_DIR = ".reggata"
DB_FILE = "database.sqlite3"
USER_CONFIG_DIR = os.path.expanduser("~") + os.sep + ".config" + os.sep + "reggata"
REGGATA_INI = "reggata.ini"
USER_CONFIG_FILE = USER_CONFIG_DIR + os.sep + REGGATA_INI

THUMBNAIL_DEFAULT_SIZE = 100