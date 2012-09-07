'''
Created on 27.08.2012
@author: vvolkov
'''
import os
from PyQt4 import QtCore
from tests.abstract_test_cases import AbstractTestCaseWithRepo
from logic.action_handlers import AddSingleItemActionHandler
from logic.abstract_gui import AbstractGui
from data.db_schema import User
from tests.tests_dialogs_facade import TestsDialogsFacade
from data.commands import GetExpungedItemCommand
from helpers import to_db_format

class TestsGuiModel():
    def __init__(self, repo, user, gui):
        self.repo = repo
        self.user = user
        self.gui = gui


class TestsGui(QtCore.QObject, AbstractGui):
    def __init__(self, repo, user, selectedFiles=[]):
        super(QtCore.QObject, self).__init__()
        self.__selectedFiles = selectedFiles
        self.receivedSignals = []
        self.__model = TestsGuiModel(repo, user, self)
        
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

    
    def _get_model(self):
        return self.__model
    
    model = property(fget=_get_model)
    
    
    
    
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
        
    def test_addFileFromOutsideOfRepo(self):
        user = User(login="user", password="")
        srcAbsPath = os.path.abspath(os.path.join(self.repo.base_path, "..", "tmp", "file.txt"))
        
        gui = TestsGui(self.repo, user, [srcAbsPath])
        dialogs = TestsDialogsFacade()
        
        handler = AddSingleItemActionHandler(gui, dialogs)
        gui.connectHandler(handler)
        
        handler.handle()
    
        
        dstRelPath = "file.txt"
        savedItemId = handler.lastAddedItemId
        try:
            uow = self.repo.createUnitOfWork()
            savedItem = uow.executeCommand(GetExpungedItemCommand(savedItemId))
            
            self.assertIsNotNone(savedItem, 
                "Item should exist")
            self.assertIsNotNone(savedItem.data_ref, 
                "Item should have a DataRef object")
            self.assertEqual(savedItem.data_ref.url_raw, to_db_format(dstRelPath), 
                "Item's file should be located in the root of repo")
            self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, savedItem.data_ref.url)),
                "Item's file should exist")
        finally:
            uow.close()
            
    
    