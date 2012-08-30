'''
Created on 27.08.2012
@author: vvolkov
'''
import unittest
from tests.abstract_test_cases import AbstractTestCaseWithRepo
from logic.action_handlers import AddSingleItemActionHandler, HandlerSignals
from gui.abstract_gui import AbstractGui
import os
from data.db_schema import User
from PyQt4 import QtCore


class TestsGui(QtCore.QObject, AbstractGui):
    def __init__(self, repo, user, selectedFiles=[]):
        super(QtCore.QObject, self).__init__()
        self.__selectedFiles = selectedFiles
        self.__repo = repo
        self.__user = user
        self.receivedSignals = []
        
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
        pass
    
    def checkActiveRepoIsNotNone(self):
        pass
            
    def checkActiveUserIsNotNone(self):
        pass



    def _get_active_repo(self):
        return self.__repo
    
    def _set_active_repo(self, repo):
        self.__repo = repo
        
    active_repo = property(_get_active_repo, 
                           _set_active_repo)
    
    
    
    def _get_active_user(self):
        return self.__user
    
    def _set_active_user(self, user):
        self.__user = user
        
    active_user = property(_get_active_user, 
                           _set_active_user)
    
    
    def _onHandlerSignals(self, handlerSignals):
        self.receivedSignals.append(handlerSignals)
    
    def _onHandlerSignal(self, handlerSignal):
        self.receivedSignals.append([handlerSignal])
    
    def connectHandler(self, handler):
        self.connect(self, QtCore.SIGNAL("handlerSignal"), self._onHandlerSignal)
        self.connect(self, QtCore.SIGNAL("handlerSignals"), self._onHandlerSignals)
        

    
class AddSingleItemActionHandlerTest(AbstractTestCaseWithRepo):
    
    def setUp(self):
        super(AddSingleItemActionHandlerTest, self).setUp()
        self.__handlerSucceeded = False
    
    def test_saveNewMinimalItem(self):
        user = User(login="user", password="")
        srcAbsPath = os.path.abspath(os.path.join(self.repo.base_path, "..", "tmp", "file.txt"))
        
        gui = TestsGui(self.repo, user, [srcAbsPath])
        handler = AddSingleItemActionHandler(gui)
        gui.connectHandler(handler)
        
        handler.handle()
        
        self.assertTrue(gui.receivedSignals[0] == HandlerSignals.ITEM_CREATED)
    

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
    