'''
Created on 23.09.2012
@author: vitvlkv
'''
import os
from PyQt4 import QtCore
from gui.common_widgets import WaitDialog
from logic.abstract_dialogs_facade import AbstractDialogsFacade


class DropFilesDialogsFacade(AbstractDialogsFacade):
    
    def __init__(self, userDialogs):
        self.__selectedFiles = []
        self.__userDialogs = userDialogs
    
    
    def setSelectedFiles(self, selectedFiles):
        self.__selectedFiles = selectedFiles
    
    
    def execItemDialog(self, item, gui, repo, dialogMode):
        return self.__userDialogs.execItemDialog(item, gui, repo, dialogMode)
    
    
    def execItemsDialog(self, items, gui, repo, dialogMode, sameDstPath):
        return self.__userDialogs.execItemsDialog(items, gui, repo, dialogMode, sameDstPath)
     
     
    def startThreadWithWaitDialog(self, thread, gui, indeterminate):
        wd = WaitDialog(gui, indeterminate)
        wd.connect(thread, QtCore.SIGNAL("finished"), wd.reject)
        wd.connect(thread, QtCore.SIGNAL("exception"), wd.exception)
        wd.connect(thread, QtCore.SIGNAL("progress"), wd.set_progress)
        wd.startWithWorkerThread(thread)
        
        
    def getOpenFileName(self, gui, textMessageForUser):
        if (len(self.__selectedFiles) == 0):
            return None
        
        fileName = self.__selectedFiles[0]
        if os.path.exists(fileName) and os.path.isfile(fileName):
            return fileName
        
        return None
    
    
    def getOpenFileNames(self, gui, textMessageForUser):
        if (len(self.__selectedFiles) == 0):
            return None
        
        fileNames = []
        for path in self.__selectedFiles:
            if os.path.exists(path) and os.path.isfile(path):
                fileNames.append(path)
        
        if (len(fileNames) == 0):
            return None
        
        return fileNames
    
    
    def getExistingDirectory(self, gui, textMessageForUser):
        if (len(self.__selectedFiles) == 0):
            return None
        
        for path in self.__selectedFiles:
            if os.path.exists(path) and os.path.isdir(path):
                return path
            
        return None
    
    