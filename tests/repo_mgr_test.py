import unittest
import os
import shutil
from repo_mgr import RepoMgr
from exceptions import NotFoundError


class GetItemTest(unittest.TestCase):

    def setUp(self):
        self.repoBasePath = "./testrepo.rgt"
        self.repoCopyBasePath = "./copy_of_testrepo.rgt"
        
        if (os.path.exists(self.repoCopyBasePath)):
            shutil.rmtree(self.repoCopyBasePath)
        shutil.copytree(self.repoBasePath, self.repoCopyBasePath)
        
        self.repo = RepoMgr(self.repoCopyBasePath)
        self.uow = self.repo.create_unit_of_work()


    def tearDown(self):        
        self.uow.close()
        self.uow = None
        self.repo = None
        shutil.rmtree(self.repoCopyBasePath)

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