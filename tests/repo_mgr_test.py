import unittest
import os
import shutil
from repo_mgr import RepoMgr
from exceptions import NotFoundError
import tests_context


class GetItemTest(unittest.TestCase):

    def setUp(self):
        self.repoBasePath = tests_context.TEST_REPO_BASE_PATH
        self.copyOfRepoBasePath = tests_context.COPY_OF_TEST_REPO_BASE_PATH
        
        if (os.path.exists(self.copyOfRepoBasePath)):
            shutil.rmtree(self.copyOfRepoBasePath)
        shutil.copytree(self.repoBasePath, self.copyOfRepoBasePath)
        
        self.repo = RepoMgr(self.copyOfRepoBasePath)
        self.uow = self.repo.create_unit_of_work()


    def tearDown(self):        
        self.uow.close()
        self.uow = None
        self.repo = None
        shutil.rmtree(self.copyOfRepoBasePath)

    def test_getExistingItem(self):
        item = self.uow.get_item(2)
        self.assertEqual(item.title, "Dont_Forget_Me_Outro_Jam_Montreal 2006.txt")
        
    def test_getNonExistingItem(self):
        self.assertRaises(NotFoundError, self.uow.get_item, (1000000000))
        
    def test_passBadIdToGetItem(self):
        self.assertRaises(NotFoundError, self.uow.get_item, ("This str is NOT a valid item id!"))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()