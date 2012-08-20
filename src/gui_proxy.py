'''
Created on 20.08.2012
@author: vlkv
'''

import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui
from PyQt4.QtCore import Qt
import os

class GuiProxy(QtCore.QObject):
    
    def __init__(self, mainWindow, selectedFiles=[], parent=None):
        super(GuiProxy, self).__init__(parent)
        self.__mainWindow = mainWindow
        self.__selectedFiles = selectedFiles
        
    def setSelectedFiles(self, selectedFiles):
        self.__selectedFiles = selectedFiles
        
    def getOpenFileName(self, textMessageForUser):
        if (len(self.__selectedFiles) == 0):
            return None
        
        fileName = self.__selectedFiles[0]
        if os.path.exists(fileName) and os.path.isfile(fileName):
            return fileName
        
        return None
    
    def getOpenFileNames(self, textMessageForUser):
        if (len(self.__selectedFiles) == 0):
            return None
        
        fileNames = []
        for path in self.__selectedFiles:
            if os.path.exists(path) and os.path.isfile(path):
                fileNames.append(path)
        
        if (len(fileNames) == 0):
            return None
        
        return fileNames
    
    def getExistingDirectory(self, textMessageForUser):
        if (len(self.__selectedFiles) == 0):
            return None
        
        for path in self.__selectedFiles:
            if os.path.exists(path) and os.path.isdir(path):
                return path
            
        return None
    
    def showMessageOnStatusBar(self, text, timeoutBeforeClear=None):
        self.__mainWindow.showMessageOnStatusBar(text, timeoutBeforeClear)
    
    def checkActiveRepoIsNotNone(self):
        self.__mainWindow.checkActiveRepoIsNotNone()
            
    def checkActiveUserIsNotNone(self):
        self.__mainWindow.checkActiveUserIsNotNone()



    def _get_active_repo(self):
        return self.__mainWindow._get_active_repo()
    
    def _set_active_repo(self, repo):
        self.__mainWindow._set_active_repo(repo)
        
    active_repo = property(_get_active_repo, 
                           _set_active_repo)
    
    
    
    def _get_active_user(self):
        return self.__mainWindow._get_active_user()
    
    def _set_active_user(self, user):
        self.__mainWindow._set_active_user(user)
        
    active_user = property(_get_active_user, 
                           _set_active_user)
    
    
        