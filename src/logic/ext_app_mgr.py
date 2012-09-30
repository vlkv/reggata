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
    def __init__(self, filesCategory, appCommandPattern, fileExtentions):
        self.filesCategory = filesCategory
        self.appCommandPattern = appCommandPattern
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
                
                self.extensions[ext] = appDescription.appCommandPattern
                
        self.extFileManagerCommandPattern = UserConfig().get('ext_file_manager')
             
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
        appCommandPattern = self.extensions.get(ext.lower(), None)
        
        if appCommandPattern is None:
            msg = QCoreApplication.translate("ext_app_mgr", 
                        "File type is not defined for {0} file extension. Edit your {1} file.", 
                        None, QCoreApplication.UnicodeUTF8)
            raise Exception(msg.format(ext, consts.USER_CONFIG_FILE))

        appCommand = self.__replaceCommandPatternKeys(appCommandPattern, 
                                                      filePath=abs_path, 
                                                      dirPath=os.path.dirname(abs_path))
        self.__createSubprocess(appCommand)


    def external_file_manager(self, abs_path):
        if self.extFileManagerCommandPattern is None:
            msg = QCoreApplication.translate("ext_app_mgr", 
                        "No external file manager command is set. Please edit your {} file.", 
                        None, QCoreApplication.UnicodeUTF8)
            raise MsgException(msg.format(consts.USER_CONFIG_FILE))
        
        appCommand = self.__replaceCommandPatternKeys(self.extFileManagerCommandPattern, 
                                                      filePath=abs_path, 
                                                      dirPath=os.path.dirname(abs_path))
        self.__createSubprocess(appCommand)
        
        
    def __replaceCommandPatternKeys(self, commandPattern, filePath, dirPath):
        result = commandPattern.replace('%f', '"' + filePath + '"')
        result = result.replace('%d', '"' + dirPath + '"')
        return result
        
        
    def __createSubprocess(self, commandWithArgs):
        args = shlex.split(commandWithArgs)
        args = self.__modifyArgsIfOnWindowsAndPathIsNetwork(args)
        logger.debug("subprocess.Popen(args), args=%s", args)
        
        #subprocess.call(args) #This call would block the current thread
        pid = subprocess.Popen(args).pid #This call would not block the current thread
        logger.info("Created subprocess with PID = %d", pid)
        
        # TODO: raise an exception if application executable file not found
        
        
    def __modifyArgsIfOnWindowsAndPathIsNetwork(self, args):
        # This is a hack... On Windows shlex fails to handle correctly network paths such as
        # \\Tiger\SYSTEM (C)\home\testrepo.rgt\file.txt
        if not sys.platform.startswith("win"):
            return args
        if args[1].startswith("\\"):
            args[1] = "\\" + args[1]
        return args


