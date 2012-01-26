import unittest
import tests_context
import os
import shutil
from repo_mgr import RepoMgr


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


class AbstractTestCaseWithRepoAndSingleUOW(unittest.TestCase):
    
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

