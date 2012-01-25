'''
Created on 25.01.2012

@author: vvolkov
'''
import unittest
import tests_context
import os
import shutil
from repo_mgr import RepoMgr
from worker_threads import DeleteGroupOfItemsThread


class AbstractTestCaseWithRepo(unittest.TestCase):
    
    def setUp(self):
        self.repoBasePath = tests_context.TEST_REPO_BASE_PATH
        self.copyOfRepoBasePath = tests_context.COPY_OF_TEST_REPO_BASE_PATH
        
        if (os.path.exists(self.copyOfRepoBasePath)):
            shutil.rmtree(self.copyOfRepoBasePath)
        shutil.copytree(self.repoBasePath, self.copyOfRepoBasePath)
        
        self.repo = RepoMgr(self.copyOfRepoBasePath)

    def tearDown(self):
        self.repo = None
        shutil.rmtree(self.copyOfRepoBasePath)


class DeleteGroupOfItemsThreadTest(AbstractTestCaseWithRepo):

    def testName(self):
        thread = DeleteGroupOfItemsThread(parent=None, repo=self.repo, item_ids=[1, 2, 3], user_login="user")
        thread.run()
        
        uow = self.repo.create_unit_of_work()
        self.assertFalse(uow.get_item(1).alive)
        self.assertFalse(uow.get_item(2).alive)
        self.assertFalse(uow.get_item(3).alive)
        uow.close()
        
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
    