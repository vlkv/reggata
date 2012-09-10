'''
Created on 27.08.2012
@author: vvolkov
'''
import os
from tests.abstract_test_cases import AbstractTestCaseWithRepo
from logic.action_handlers import AddSingleItemActionHandler, AddManyItemsActionHandler,\
    AddManyItemsRecursivelyActionHandler
from data.db_schema import User
from tests.tests_dialogs_facade import TestsDialogsFacade
from data.commands import GetExpungedItemCommand
from helpers import to_db_format
from logic.abstract_tool import AbstractTool
from logic.abstract_tool_gui import AbstractToolGui
from PyQt4 import QtCore

class TestsToolModel(AbstractTool):
    '''
        This is a replacement for ItemsTable in tests.
    '''
    def __init__(self, repo, user):
        super(TestsToolModel, self).__init__()
        self.repo = repo
        self.user = user
        self._gui = None
        
    def checkActiveRepoIsNotNone(self):
        pass
            
    def checkActiveUserIsNotNone(self):
        pass
    
    def _getGui(self):
        if self._gui is None:
            self._gui = TestsToolGui(self)
        return self._gui
    gui = property(fget=_getGui)
    

class TestsToolGui(QtCore.QObject, AbstractToolGui):
    
    def __init__(self, model):
        super(TestsToolGui, self).__init__()
        self._model = model
    
    def _get_model(self):
        return self._model
    model = property(fget=_get_model)

    
class AddItemsActionHandlerTest(AbstractTestCaseWithRepo):
    
    def setUp(self):
        super(AddItemsActionHandlerTest, self).setUp()
        
    def test_addFileFromOutsideOfRepo(self):
        user = User(login="user", password="")
        srcAbsPath = os.path.abspath(os.path.join(self.repo.base_path, "..", "tmp", "file.txt"))
        dstRelPath = "file.txt"
        
        self.assertFalse(os.path.exists(os.path.join(self.repo.base_path, dstRelPath)), 
            "Target file should not be already in the repo root")
        
        
        tool = TestsToolModel(self.repo, user)
        dialogs = TestsDialogsFacade(selectedFiles=[srcAbsPath])
        handler = AddSingleItemActionHandler(tool, dialogs)
        handler.handle()    
        
        self.assertIsNotNone(handler.lastSavedItemId)
        try:
            uow = self.repo.createUnitOfWork()
            savedItem = uow.executeCommand(GetExpungedItemCommand(handler.lastSavedItemId))
            
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
            
            
    def test_addTwoFilesFromOutsideOfRepo(self):
        user = User(login="user", password="")
        srcAbsPath = []
        dstRelPath = []
        srcAbsPath.append(os.path.abspath(os.path.join(self.repo.base_path, "..", "tmp", "file.txt")))
        dstRelPath.append("file.txt")
        srcAbsPath.append(os.path.abspath(os.path.join(self.repo.base_path, "..", "tmp", "grub.conf")))
        dstRelPath.append("grub.conf")
        
        self.assertFalse(os.path.exists(os.path.join(self.repo.base_path, dstRelPath[0])), 
            "Target file should not be already in the repo root")
        self.assertFalse(os.path.exists(os.path.join(self.repo.base_path, dstRelPath[1])), 
            "Target file should not be already in the repo root")
        
        
        tool = TestsToolModel(self.repo, user)
        dialogs = TestsDialogsFacade(selectedFiles=[srcAbsPath[0], srcAbsPath[1]])
        handler = AddManyItemsActionHandler(tool, dialogs)
        handler.handle()
        
        
        self.assertEqual(len(dstRelPath), len(handler.lastSavedItemIds))
        for i, savedItemId in enumerate(handler.lastSavedItemIds):
            try:
                uow = self.repo.createUnitOfWork()
                savedItem = uow.executeCommand(GetExpungedItemCommand(savedItemId))
                
                self.assertIsNotNone(savedItem, 
                    "Item should exist")
                self.assertIsNotNone(savedItem.data_ref, 
                    "Item should have a DataRef object")
                self.assertEqual(savedItem.data_ref.url_raw, to_db_format(dstRelPath[i]), 
                    "Item's file should be located in the root of repo")
                self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, savedItem.data_ref.url)),
                    "Item's file should exist")
            finally:
                uow.close()
            
    def test_addRecursivelyDirFromOutsideOfRepo(self):
        user = User(login="user", password="")
        srcDirAbsPath = os.path.abspath(os.path.join(self.repo.base_path, "..", "tmp"))
        
        dstRelPaths = []
        for root, dirs, files in os.walk(srcDirAbsPath):
            for file in files:
                dstRelPaths.append(os.path.relpath(os.path.join(root, file), srcDirAbsPath))
        
        
        tool = TestsToolModel(self.repo, user)
        dialogs = TestsDialogsFacade(selectedFiles=[srcDirAbsPath])
        handler = AddManyItemsRecursivelyActionHandler(tool, dialogs)
        handler.handle()
        
        
        self.assertEqual(len(handler.lastSavedItemIds), len(dstRelPaths))
        for i, savedItemId in enumerate(handler.lastSavedItemIds):
            try:
                uow = self.repo.createUnitOfWork()
                savedItem = uow.executeCommand(GetExpungedItemCommand(savedItemId))
                
                self.assertIsNotNone(savedItem, 
                    "Item should exist")
                self.assertIsNotNone(savedItem.data_ref, 
                    "Item should have a DataRef object")
                self.assertEqual(savedItem.data_ref.url_raw, to_db_format(dstRelPaths[i]), 
                    "Item's file should be located in the root of repo")
                self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, savedItem.data_ref.url)),
                    "Item's file should exist")
            finally:
                uow.close()
            
    