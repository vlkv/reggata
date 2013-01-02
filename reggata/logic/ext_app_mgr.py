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
import string
from PyQt4 import QtCore

logger = logging.getLogger(consts.ROOT_LOGGER + "." + __name__)


class FileExtentionMultiplyRegisteredError(Exception):
    def __init__(self, msg=None):
        super(FileExtentionMultiplyRegisteredError, self).__init__(msg)

class NameContainsWhitespacesError(Exception):
    def __init__(self, msg=None):
        super(NameContainsWhitespacesError, self).__init__(msg)


class ExtAppDescription(object):
    def __init__(self, filesCategory, appCommandPattern, fileExtentions):
        self.filesCategory = filesCategory
        self.appCommandPattern = appCommandPattern
        self.fileExtentions = fileExtentions

class ExtAppMgrState(object):
    def __init__(self, appDescriptions=[], extFileMgrCommandPattern=None):
        self.appDescriptions = appDescriptions         
        self.extFileMgrCommandPattern = extFileMgrCommandPattern
        
    def raiseErrorIfNotValid(self):
        # Check that every extention doesn't included in more than one category
        for appDescription in self.appDescriptions:
            for fileExt in appDescription.fileExtentions:
                for appDescription2 in self.appDescriptions:
                    if appDescription2.filesCategory == appDescription.filesCategory:
                        continue
                    if fileExt in appDescription2.fileExtentions:
                        raise FileExtentionMultiplyRegisteredError(
                            "File extention '{0}' is registered in two categories: '{1}' and '{2}'. " 
                            "But it should be registered in only one category."
                            .format(fileExt, appDescription.filesCategory, appDescription2.filesCategory))
        
        #Category names should not contain whitespaces
        for appDescription in self.appDescriptions:
            for symbol in string.whitespace:
                if symbol in appDescription.filesCategory:
                    raise NameContainsWhitespacesError("Category name '{}' should not contain whitespaces."
                                                       .format(appDescription.filesCategory))
            
                
        


class ExtAppMgr(QtCore.QObject):
    '''
        This class invokes preferred external applications to open repository files.
    Preferred applications are configured in text file reggata.conf.
    '''

    def __init__(self, parent=None):
        super(ExtAppMgr, self).__init__(parent)
        
        self.updateState()
             

    def updateState(self):
        self.__state = ExtAppMgr.readCurrentState()
            
        # Key - file extension (in lowercase), Value - external app executable
        extentionsDict = dict()
        for appDescription in self.__state.appDescriptions:
            for ext in appDescription.fileExtentions:
                ext = ext.lower()
                
                if ext in extentionsDict.keys():
                    msg = QCoreApplication.translate("ext_app_mgr",
                        "File extension {} cannot be in more than one file_type group.", 
                        None, QCoreApplication.UnicodeUTF8)
                    raise ValueError(msg.format(ext))
                
                extentionsDict[ext] = appDescription.appCommandPattern
        self.__extensions = extentionsDict
             
             
    @staticmethod
    def readCurrentState():
        filesCategories = eval(UserConfig().get('ext_app_mgr_file_types', "[]"))
        
        appDescriptions = []
        for filesCategory in filesCategories:
            extentions = eval(UserConfig().get('ext_app_mgr.{}.extensions'
                                                      .format(filesCategory)))
            appCmd = UserConfig().get("ext_app_mgr.{}.command"
                                       .format(filesCategory))
            appDescriptions.append(ExtAppDescription(filesCategory, appCmd, extentions))
        
        extFileManagerCommandPattern = UserConfig().get('ext_file_manager')
        
        state = ExtAppMgrState(appDescriptions, 
                               extFileManagerCommandPattern)
        return state
    
    
    @staticmethod
    def setCurrentState(extAppMgrState):
        extAppMgrState.raiseErrorIfNotValid()
        
        stateDict = dict()
        categories = []
        for appDescription in extAppMgrState.appDescriptions:
            category = appDescription.filesCategory
            categories.append(category)
            stateDict["ext_app_mgr.{}.command".format(category)] = appDescription.appCommandPattern
            stateDict["ext_app_mgr.{}.extensions".format(category)] = appDescription.fileExtentions
        
        stateDict["ext_app_mgr_file_types"] = categories
        stateDict["ext_file_manager"] = extAppMgrState.extFileMgrCommandPattern
        
        UserConfig().storeAll(stateDict)
    
        
             
    def openFileWithExtApp(self, abs_path):
    
        _, ext = os.path.splitext(abs_path)
        appCommandPattern = self.__extensions.get(ext.lower(), None)
        
        if appCommandPattern is None:
            msg = QCoreApplication.translate("ext_app_mgr", 
                        "External application for {0} file extension is not set. "
                        "Please, go to 'Main Menu -> Repository -> Manage External Applications' "
                        "and configure it", 
                        None, QCoreApplication.UnicodeUTF8)
            raise Exception(msg.format(ext))

        appCommand = self.__replaceCommandPatternKeys(appCommandPattern, 
                                                      filePath=abs_path, 
                                                      dirPath=os.path.dirname(abs_path))
        self.__createSubprocess(appCommand)


    def openContainingDirWithExtAppManager(self, abs_path):
        if self.__state.extFileMgrCommandPattern is None:
            msg = QCoreApplication.translate("ext_app_mgr", 
                        "No external file manager command is set. Please edit your {} file.", 
                        None, QCoreApplication.UnicodeUTF8)
            raise MsgException(msg.format(consts.USER_CONFIG_FILE))
        
        appCommand = self.__replaceCommandPatternKeys(self.__state.extFileMgrCommandPattern, 
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


