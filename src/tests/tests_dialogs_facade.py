'''
Created on 28.08.2012
@author: vvolkov
'''
from logic.abstract_dialogs_facade import AbstractDialogsFacade
import os

class TestsDialogsFacade(AbstractDialogsFacade):
    
    def __init__(self, selectedFiles=[]):
        self.__selectedFiles = selectedFiles
    
    
    def execUserDialog(self, user, gui, dialogMode):
        return True

    def execChangeUserPasswordDialog(self, user, gui):
        return True
    
    def execItemDialog(self, item, gui, repo, dialogMode):
        
        if item.data_ref is not None:
            item.data_ref.srcAbsPath = item.data_ref.url 
            item.data_ref.dstRelPath = os.path.basename(item.data_ref.url)
        return True
    
    def execItemsDialog(self, items, gui, repo, dialogMode, sameDstPath):
        
        for item in items:
            if item.data_ref is not None:
                item.data_ref.srcAbsPath = item.data_ref.url 
                item.data_ref.dstRelPath = os.path.basename(item.data_ref.url)
        return True
     
     
    def startThreadWithWaitDialog(self, thread, gui, indeterminate):
        thread.run()
        
        
        
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
    
    