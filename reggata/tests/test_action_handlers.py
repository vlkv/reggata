'''
Created on 27.08.2012
@author: vvolkov
'''
import os
from PyQt4 import QtCore
from reggata.helpers import to_db_format
from reggata.data.db_schema import User
from reggata.data.commands import GetExpungedItemCommand
from reggata.logic.abstract_tool import AbstractTool
from reggata.logic.abstract_tool_gui import AbstractToolGui
from reggata.logic.common_action_handlers import EditItemActionHandler
from reggata.logic.items_table_action_handlers import AddItemsActionHandler,\
    DeleteItemActionHandler, RebuildItemThumbnailActionHandler
from reggata.tests.abstract_test_cases import AbstractTestCaseWithRepo
from reggata.tests.tests_context import itemWithTagsAndFields, itemWithFile, itemWithoutFile
from reggata.tests.tests_dialogs_facade import TestsDialogsFacade
import time


class TestsToolModel(AbstractTool):
    '''
        This is a replacement for ItemsTable in tests.
    '''
    def __init__(self, repo, user):
        super(TestsToolModel, self).__init__()
        self.repo = repo
        self.user = user
        self._gui = None
        self.itemsLock = QtCore.QReadWriteLock()

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
        self._selectedItemIds = []
        self._items = []

    def _get_model(self):
        return self._model
    model = property(fget=_get_model)

    def setItems(self, items):
        self._items = items

    def selectedItemIds(self):
        return self._selectedItemIds

    def setSelectedItemIds(self, itemIds):
        self._selectedItemIds = itemIds

    def selectedRows(self):
        return [x for x in range(len(self._selectedItemIds))]

    def itemAtRow(self, row):
        foundItems = [item for item in self._items if item.id == self._selectedItemIds[row]]
        assert len(foundItems) == 1
        return foundItems[0]



class AddItemsActionHandlerTest(AbstractTestCaseWithRepo):

    def test_addFileFromOutsideOfRepo(self):
        user = User(login="user", password="")
        srcAbsPath = os.path.abspath(os.path.join(self.repo.base_path, "..", "tmp", "file.txt"))
        dstRelPath = "file.txt"

        self.assertFalse(os.path.exists(os.path.join(self.repo.base_path, dstRelPath)),
            "Target file should not be already in the repo root")


        tool = TestsToolModel(self.repo, user)
        dialogs = TestsDialogsFacade(selectedFiles=[srcAbsPath])
        handler = AddItemsActionHandler(tool, dialogs)
        handler.handle()

        self.assertEqual(len(handler.lastSavedItemIds), 1)
        try:
            uow = self.repo.createUnitOfWork()
            savedItem = uow.executeCommand(GetExpungedItemCommand(handler.lastSavedItemIds[0]))

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
        handler = AddItemsActionHandler(tool, dialogs)
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
                dstRelPath = os.path.relpath(os.path.join(root, file), os.path.join(srcDirAbsPath, ".."))
                dstRelPaths.append(dstRelPath)

        tool = TestsToolModel(self.repo, user)
        dialogs = TestsDialogsFacade(selectedFiles=[srcDirAbsPath])
        handler = AddItemsActionHandler(tool, dialogs)
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
                    "Item's file not found in repo")
                self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, savedItem.data_ref.url)),
                    "Item's file should exist")
            finally:
                uow.close()



class RemoveAllTagsFromItemDialogsFacade(TestsDialogsFacade):
    def execItemDialog(self, item, gui, repo, dialogMode):
        del item.item_tags[:]
        return True

    def execItemsDialog(self, items, gui, repo, dialogMode, sameDstPath):
        for item in items:
            del item.item_tags[:]
        return True


class EditItemsActionHandlerTest(AbstractTestCaseWithRepo):

    def test_editSingleItem(self):
        user = User(login="user", password="")

        tool = TestsToolModel(self.repo, user)
        tool.gui.setSelectedItemIds([itemWithTagsAndFields.id])
        dialogs = RemoveAllTagsFromItemDialogsFacade()

        handler = EditItemActionHandler(tool, dialogs)
        handler.handle()

        try:
            uow = self.repo.createUnitOfWork()
            editedItem = uow.executeCommand(GetExpungedItemCommand(itemWithTagsAndFields.id))

            self.assertIsNotNone(editedItem,
                "Item should exist")
            self.assertTrue(editedItem.alive,
                "Item should be alive")
            self.assertEqual(len(editedItem.item_tags), 0,
                "Item should have no tags, because we've just removed them all")
        finally:
            uow.close()

    def test_editThreeItems(self):
        user = User(login="user", password="")

        tool = TestsToolModel(self.repo, user)
        selectedItemIds = [itemWithTagsAndFields.id,
                           itemWithFile.id,
                           itemWithoutFile.id]
        tool.gui.setSelectedItemIds(selectedItemIds)
        dialogs = RemoveAllTagsFromItemDialogsFacade()

        handler = EditItemActionHandler(tool, dialogs)
        handler.handle()

        for itemId in selectedItemIds:
            try:
                uow = self.repo.createUnitOfWork()
                editedItem = uow.executeCommand(GetExpungedItemCommand(itemId))

                self.assertIsNotNone(editedItem,
                    "Item should exist")
                self.assertTrue(editedItem.alive,
                    "Item should be alive")
                self.assertEqual(len(editedItem.item_tags), 0,
                    "Item should have no tags, because we've just removed them all")
            finally:
                uow.close()


class RebuildThumbnailActionHandlerTest(AbstractTestCaseWithRepo):

    def test_rebuildThumbnail(self):
        user = User(login="user", password="")

        tool = TestsToolModel(self.repo, user)
        selectedItemIds = [itemWithTagsAndFields.id,
                           itemWithFile.id,
                           itemWithoutFile.id]
        selectedItems = []
        for itemId in selectedItemIds:
            try:
                uow = self.repo.createUnitOfWork()
                item = uow.executeCommand(GetExpungedItemCommand(itemId))
                self.assertIsNotNone(item)
                selectedItems.append(item)
            finally:
                uow.close()

        tool.gui.setItems(selectedItems)
        tool.gui.setSelectedItemIds(selectedItemIds)

        handler = RebuildItemThumbnailActionHandler(tool)
        handler.handle()
        # Maybe we should add more checks here... but
        # The main goal for this test is to check that nothing crashes in the action handler itself
        # TODO: use some image files in this test and check that thumbnails were builded!
        time.sleep(1)


class DeleteItemActionHandlerTest(AbstractTestCaseWithRepo):

    def test_deleteItem(self):
        user = User(login="user", password="")

        tool = TestsToolModel(self.repo, user)

        itemId = itemWithTagsAndFields.id
        tool.gui.setSelectedItemIds([itemId])
        dialogs = TestsDialogsFacade()

        handler = DeleteItemActionHandler(tool, dialogs)
        handler.handle()

        try:
            uow = self.repo.createUnitOfWork()
            deletedItem = uow.executeCommand(GetExpungedItemCommand(itemId))
            self.assertFalse(deletedItem.alive,
                "Deleted item still exists, but item.alive is False")
            self.assertIsNone(deletedItem.data_ref,
                "Deleted item should have None DataRef object")
            self.assertFalse(os.path.exists(os.path.join(self.repo.base_path, itemWithTagsAndFields.relFilePath)),
                "File of deleted Item should be deleted on filesystem")
        finally:
            uow.close()


class OpenItemActionHandlerTest(AbstractTestCaseWithRepo):
    #TODO: implement test of OpenItemActionHandler
    pass
