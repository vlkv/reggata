import unittest
import os
from tests import test_memento, test_helpers, test_repo_mgr, test_worker_threads


class TestRunner():
    def __init__(self):
        self.suite = unittest.TestSuite()
        self.addAllTestCases()
    
    def addAllTestCases(self):
        self.addTestCase(test_memento.ItemSerializationSimpleTest)
        self.addTestCase(test_memento.ItemSerializationTest)
        
        self.addTestCase(test_helpers.IsNoneOrEmptyTest)
        
        self.addTestCase(test_repo_mgr.GetItemTest)
        self.addTestCase(test_repo_mgr.DeleteItemTest)
        self.addTestCase(test_repo_mgr.SaveNewItemTest)
        self.addTestCase(test_repo_mgr.UpdateItemTest)
        
        self.addTestCase(test_worker_threads.DeleteGroupOfItemsThreadTest)

    def addTestCase(self, testCaseCls):
        self.suite.addTests(unittest.TestLoader().loadTestsFromTestCase(testCaseCls))
        
    def runAllTests(self):
        unittest.TextTestRunner(verbosity=2).run(self.suite)



def runTestsFromList():
    testRunner = TestRunner()
    testRunner.runAllTests()

def discoverAndRunAllTests():
    loader = unittest.TestLoader()
    tests = loader.discover(os.path.join(dirAbsPath, ".."))
    testRunner = unittest.runner.TextTestRunner(verbosity=2)
    testRunner.run(tests)

if __name__ == '__main__':
    print("Current dir is " + os.path.abspath("."))
    
    fileAbsPath = os.path.abspath(__file__)
    dirAbsPath = os.path.dirname(fileAbsPath)
    print("Directory of runtests.py is " + dirAbsPath)
    
    try:
        print("Trying to discover and run all tests...")
        discoverAndRunAllTests()
    except AttributeError as err:
        print("Tests discovering failed (perhaps you have old python version <= 3.1")
        print("Running all tests from predefined list.")
        runTestsFromList()
    finally:
        print("Done")

    
    
    

    
