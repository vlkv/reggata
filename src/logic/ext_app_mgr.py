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

Created on 05.12.2010

@author: vlkv
'''
from user_config import UserConfig
import os
import consts
import subprocess
import shlex
from errors import MsgException
import logging
from PyQt4.QtCore import QCoreApplication 
import sys

logger = logging.getLogger(consts.ROOT_LOGGER + "." + __name__)


class ExtAppMgr(object):
    '''
    This class invokes preferred external applications to open repository files.
    Preferred applications are configured in text file reggata.conf.
    See also reggata.conf.template file as an example of such config.
    '''

    def __init__(self):

        file_types_list = eval(UserConfig().get('ext_app_mgr_file_types', "[]"))
        
        #Key - name of the files group, Value - list of file extensions
        self.file_types = dict()
        for file_type in file_types_list:
            self.file_types[file_type] = eval(UserConfig().get('ext_app_mgr.{}.extensions'.format(file_type)))
            
        #Key - file extension (in lowercase), Value - name of the files group
        self.extensions = dict()
        for type, ext_list in self.file_types.items():             
            for ext in ext_list:
                ext = ext.lower()
                if ext in self.extensions.keys():
                    msg = QCoreApplication.translate("ext_app_mgr",
                        "File extension {} cannot be in more than one file_type group.", 
                        None, QCoreApplication.UnicodeUTF8)
                    raise ValueError(msg.format(ext))
                self.extensions[ext] = type
                
        self.ext_file_manager_command = UserConfig().get('ext_file_manager')
             
    def invoke(self, abs_path, file_type=None):
        if not file_type:
            name, ext = os.path.splitext(abs_path)
            file_type = self.extensions.get(ext.lower())
        
        if not file_type:
            msg = QCoreApplication.translate("ext_app_mgr", 
                        "File type is not defined for {0} file extension. Edit your {1} file.", 
                        None, QCoreApplication.UnicodeUTF8)
            raise Exception(msg.format(ext, consts.USER_CONFIG_FILE))
        
        command = UserConfig().get("ext_app_mgr.{}.command".format(file_type))
        if not command:
            msg = QCoreApplication.translate("ext_app_mgr", 
                        "Command for file_type {0} not found. Edit your {1} file.", 
                        None, QCoreApplication.UnicodeUTF8)
            raise Exception(msg.format(file_type, consts.USER_CONFIG_FILE))

        command = command.replace('%d', '"' + os.path.dirname(abs_path) + '"')
        command = command.replace('%f', '"' + abs_path + '"')
        args = shlex.split(command)
        args = self.__modifyArgsIfOnWindowsAndPathIsNetwork(args)
        logger.debug("subprocess.Popen(args), args=%s", args)
        
        #subprocess.call(args) #This call would block the current thread
        pid = subprocess.Popen(args).pid #This call would not block the current thread
        logger.info("Created subprocess with PID = %d", pid)

    def external_file_manager(self, abs_path):
        if self.ext_file_manager_command is None:
            msg = QCoreApplication.translate("ext_app_mgr", 
                        "No external file manager command is set. Please edit your {} file.", 
                        None, QCoreApplication.UnicodeUTF8)
            raise MsgException(msg.format(consts.USER_CONFIG_FILE))
        
        command = self.ext_file_manager_command
        command = command.replace('%d', '"' + os.path.dirname(abs_path) + '"')
        command = command.replace('%f', '"' + abs_path + '"')
        args = shlex.split(command)
        args = self.__modifyArgsIfOnWindowsAndPathIsNetwork(args)
        logger.debug("subprocess.Popen(args), args=%s", args)
        
        pid = subprocess.Popen(args).pid 
        logger.info("Created subprocess with PID = %d", pid)
        
        
    def __modifyArgsIfOnWindowsAndPathIsNetwork(self, args):
        # This is a hack... On Windows shlex fails to handle correctly network paths such as
        # \\Tiger\SYSTEM (C)\home\testrepo.rgt\file.txt
        if not sys.platform.startswith("win"):
            return args
        if args[1].startswith("\\"):
            args[1] = "\\" + args[1]
        return args


