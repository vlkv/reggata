import unittest
import os
from exceptions import NotFoundError, AccessError
from abstract_test_cases import AbstractTestCaseWithRepoAndSingleUOW,\
    AbstractTestCaseWithRepo
from tests_context import COPY_OF_TEST_REPO_BASE_PATH, existingAliveItem, nonExistingItem
from repo_mgr import UnitOfWork
from db_schema import HistoryRec, Item
import helpers


class GetItemTest(AbstractTestCaseWithRepoAndSingleUOW):
    def test_getExistingItem(self):
        item = self.uow.get_item(existingAliveItem.id)
        self.assertEqual(item.title, existingAliveItem.title)
        
    def test_getNonExistingItem(self):
        self.assertRaises(NotFoundError, self.uow.get_item, (nonExistingItem.id))
        
    def test_passBadIdToGetItem(self):
        self.assertRaises(NotFoundError, self.uow.get_item, ("This str is NOT a valid item id!"))


class SaveNewItemTest(AbstractTestCaseWithRepo):
    
    def test_saveNewMinimalItem(self):
        # "Minimal item" here means that this item has no data references, tags or fields
        item = Item("user", "Minimal Item")
        try:
            uow = self.repo.create_unit_of_work()
            self.savedItemId = uow.saveNewItem(item)
        finally:
            uow.close()
            
        try:
            uow = self.repo.create_unit_of_work()
            savedItem = uow.get_item(self.savedItemId)
            self.assertEqual(savedItem.title, item.title)
            
            histRec = UnitOfWork._find_item_latest_history_rec(uow.session, savedItem)
            self.assertIsNotNone(histRec)
            self.assertEqual(histRec.operation, HistoryRec.CREATE)
            self.assertEqual(histRec.user_login, savedItem.user_login)
            self.assertIsNone(histRec.parent1_id)
            self.assertIsNone(histRec.parent2_id)
        finally:
            uow.close()
            
    def test_saveNewItemByNonExistentUserLogin(self):
        item = Item("such_user_login_doesn't_exist", "Item's title")
        try:
            uow = self.repo.create_unit_of_work()
            self.assertRaises(AccessError, uow.saveNewItem, (item))
            
        finally:
            uow.close()
            
    def test_saveNewItemByNullUserLogin(self):
        item = Item(None, "Item's title")
        try:
            uow = self.repo.create_unit_of_work()
            self.assertRaises(AccessError, uow.saveNewItem, (item))
        finally:
            uow.close()
            
    def test_saveNewItemByEmptyUserLogin(self):
        item = Item("", "Item's title")
        try:
            uow = self.repo.create_unit_of_work()
            self.assertRaises(AccessError, uow.saveNewItem, (item))
        finally:
            uow.close()

    
    def test_saveNewItemWithFileOutsizeRepo(self):
        '''
        User wants to add an external file into the repo. File is copied to the repo.
        '''
        item = Item("user", "Item's title")
        self.srcAbsPath = os.path.abspath(os.path.join(self.repo.base_path, "..", "tmp", "file.txt"))
        self.dstRelPath = os.path.join("dir1", "dir2", "dir3", "newFile.txt")
        try:
            uow = self.repo.create_unit_of_work()
            self.savedItemId = uow.saveNewItem(item, self.srcAbsPath, self.dstRelPath)
        finally:
            uow.close()
            
        try:
            uow = self.repo.create_unit_of_work()
            savedItem = uow.get_item(self.savedItemId)
            self.assertEqual(savedItem.title, item.title)
            
            self.assertIsNotNone(savedItem.data_ref)
            self.assertEqual(savedItem.data_ref.url_raw, helpers.to_db_format(self.dstRelPath))
            self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, savedItem.data_ref.url)))
            
            histRec = UnitOfWork._find_item_latest_history_rec(uow.session, savedItem)
            self.assertIsNotNone(histRec)
            self.assertEqual(histRec.operation, HistoryRec.CREATE)
            self.assertEqual(histRec.user_login, savedItem.user_login)
            self.assertIsNone(histRec.parent1_id)
            self.assertIsNone(histRec.parent2_id)
            
            self.assertTrue(os.path.exists(self.srcAbsPath))
        finally:
            uow.close()
    

class DeleteItemTest(AbstractTestCaseWithRepo):
    def test_deleteExistingItemWithExistingPhysicalFileByOwner(self):
        userThatDeletesItem = existingAliveItem.ownerUserLogin
        try:
            uow = self.repo.create_unit_of_work()
            itemBeforeDelete = uow.get_item(existingAliveItem.id)
            uow.delete_item(existingAliveItem.id, 
                        userThatDeletesItem, 
                        delete_physical_file=True)
        finally:
            uow.close()
        
        try:
            uow = self.repo.create_unit_of_work()
            deletedItem = uow.get_item(existingAliveItem.id)
            self.assertFalse(deletedItem.alive)
            self.assertIsNone(deletedItem.data_ref)
            
            #NOTE that tags/fields collections are not cleared, as you might expect
            self.assertTrue(len(deletedItem.item_tags) >= 0)
            self.assertTrue(len(deletedItem.item_fields) >= 0)
            
            histRec = UnitOfWork._find_item_latest_history_rec(uow.session, itemBeforeDelete)
            self.assertIsNotNone(histRec)
            self.assertEqual(histRec.operation, HistoryRec.DELETE)
            self.assertEqual(histRec.user_login, userThatDeletesItem)
            self.assertIsNotNone(histRec.parent1_id)
            self.assertIsNone(histRec.parent2_id)
            #Should we test any other conditions?
            
        finally:
            uow.close()
        self.assertFalse(os.path.exists(os.path.join(COPY_OF_TEST_REPO_BASE_PATH, existingAliveItem.relFilePath)))
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()