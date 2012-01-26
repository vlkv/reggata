import unittest
import os
from exceptions import NotFoundError
from abstract_test_cases import AbstractTestCaseWithRepoAndSingleUOW,\
    AbstractTestCaseWithRepo
from tests_context import COPY_OF_TEST_REPO_BASE_PATH, existingAliveItem, nonExistingItem
from repo_mgr import UnitOfWork
from db_schema import HistoryRec


class GetItemTest(AbstractTestCaseWithRepoAndSingleUOW):
    def test_getExistingItem(self):
        item = self.uow.get_item(existingAliveItem.id)
        self.assertEqual(item.title, existingAliveItem.title)
        
    def test_getNonExistingItem(self):
        self.assertRaises(NotFoundError, self.uow.get_item, (nonExistingItem.id))
        
    def test_passBadIdToGetItem(self):
        self.assertRaises(NotFoundError, self.uow.get_item, ("This str is NOT a valid item id!"))



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