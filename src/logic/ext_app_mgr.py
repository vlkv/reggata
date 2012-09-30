# -*- coding: utf-8 -*-
'''
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

class ExtAppDescription(object):
    def __init__(self, filesCategory, appExecutable, fileExtentions):
        self.filesCategory = filesCategory
        self.appExecutable = appExecutable
        self.fileExtentions = fileExtentions
        
        

class ExtAppMgr(object):
    '''
        This class invokes preferred external applications to open repository files.
    Preferred applications are configured in text file reggata.conf.
    See also reggata_default_conf.py file as an example.
    '''

    def __init__(self):

        self.appDescriptions = ExtAppMgr.currentConfig()
            
        # Key - file extension (in lowercase), Value - external app executable
        self.extensions = dict()
        for appDescription in self.appDescriptions:
            for ext in appDescription.fileExtentions:
                ext = ext.lower()
                
                if ext in self.extensions.keys():
                    msg = QCoreApplication.translate("ext_app_mgr",
                        "File extension {} cannot be in more than one file_type group.", 
                        None, QCoreApplication.UnicodeUTF8)
                    raise ValueError(msg.format(ext))
                
                self.extensions[ext] = appDescription.appExecutable
                
        self.ext_file_manager_command = UserConfig().get('ext_file_manager')
             
    @staticmethod
    def currentConfig():
        filesCategories = eval(UserConfig().get('ext_app_mgr_file_types', "[]"))
        
        result = []
        for filesCategory in filesCategories:
            extentions = eval(UserConfig().get('ext_app_mgr.{}.extensions'
                                                      .format(filesCategory)))
            appCmd = UserConfig().get("ext_app_mgr.{}.command"
                                       .format(filesCategory))
            result.append(ExtAppDescription(filesCategory, appCmd, extentions))
        return result
    
        
             
    def invoke(self, abs_path):
    
        _, ext = os.path.splitext(abs_path)
        appExecutable = self.extensions.get(ext.lower(), None)
        
        if appExecutable is None:
            msg = QCoreApplication.translate("ext_app_mgr", 
                        "File type is not defined for {0} file extension. Edit your {1} file.", 
                        None, QCoreApplication.UnicodeUTF8)
            raise Exception(msg.format(ext, consts.USER_CONFIG_FILE))
        
#        if not os.path.exists(appExecutable):
#            msg = QCoreApplication.translate("ext_app_mgr", 
#                        "File not found {0}.", 
#                        None, QCoreApplication.UnicodeUTF8)
#            raise Exception(msg.format(appExecutable))
            

        appExecutable = appExecutable.replace('%d', '"' + os.path.dirname(abs_path) + '"')
        appExecutable = appExecutable.replace('%f', '"' + abs_path + '"')
        self.__createSubprocess(appExecutable)


    def external_file_manager(self, abs_path):
        if self.ext_file_manager_command is None:
            msg = QCoreApplication.translate("ext_app_mgr", 
                        "No external file manager command is set. Please edit your {} file.", 
                        None, QCoreApplication.UnicodeUTF8)
            raise MsgException(msg.format(consts.USER_CONFIG_FILE))
        
        command = self.ext_file_manager_command
        command = command.replace('%d', '"' + os.path.dirname(abs_path) + '"')
        command = command.replace('%f', '"' + abs_path + '"')
        self.__createSubprocess(command)
        
        
    def __createSubprocess(self, commandWithArgs):
        args = shlex.split(commandWithArgs)
        args = self.__modifyArgsIfOnWindowsAndPathIsNetwork(args)
        logger.debug("subprocess.Popen(args), args=%s", args)
        
        #subprocess.call(args) #This call would block the current thread
        pid = subprocess.Popen(args).pid #This call would not block the current thread
        logger.info("Created subprocess with PID = %d", pid)
        
        
    def __modifyArgsIfOnWindowsAndPathIsNetwork(self, args):
        # This is a hack... On Windows shlex fails to handle correctly network paths such as
        # \\Tiger\SYSTEM (C)\home\testrepo.rgt\file.txt
        if not sys.platform.startswith("win"):
            return args
        if args[1].startswith("\\"):
            args[1] = "\\" + args[1]
        return args


