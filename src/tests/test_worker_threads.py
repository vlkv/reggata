'''
Created on 25.01.2012
@author: vvolkov
'''
from logic.worker_threads import DeleteGroupOfItemsThread
from tests.abstract_test_cases import AbstractTestCaseWithRepo
from data.commands import GetExpungedItemCommand

class DeleteGroupOfItemsThreadTest(AbstractTestCaseWithRepo):

    def testName(self):
        thread = DeleteGroupOfItemsThread(parent=None, 
                                          repo=self.repo, 
                                          item_ids=[1, 2, 3], 
                                          user_login="user")
        thread.run()
        
        try:
            uow = self.repo.createUnitOfWork()
            self.assertFalse(uow.executeCommand(GetExpungedItemCommand(1)).alive)
            self.assertFalse(uow.executeCommand(GetExpungedItemCommand(2)).alive)
            self.assertFalse(uow.executeCommand(GetExpungedItemCommand(3)).alive)            
        finally:
            uow.close()
    