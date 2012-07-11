'''
Created on 25.01.2012

@author: vvolkov
'''
import unittest
from repo_mgr import *
from worker_threads import DeleteGroupOfItemsThread
from abstract_test_cases import AbstractTestCaseWithRepo


class DeleteGroupOfItemsThreadTest(AbstractTestCaseWithRepo):

    def testName(self):
        thread = DeleteGroupOfItemsThread(parent=None, repo=self.repo, item_ids=[1, 2, 3], user_login="user")
        thread.run()
        
        try:
            uow = self.repo.create_unit_of_work()
            self.assertFalse(uow.executeCommand(GetExpungedItemCommand(1)).alive)
            self.assertFalse(uow.executeCommand(GetExpungedItemCommand(2)).alive)
            self.assertFalse(uow.executeCommand(GetExpungedItemCommand(3)).alive)            
        finally:
            uow.close()
        
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
    