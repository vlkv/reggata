import unittest
import os
from tests import test_memento, test_helpers, test_repo_mgr, test_worker_threads,\
    test_action_handlers, test_items_integrity

class TestsDiscoverIsNotAvailableError(Exception):
    pass
    

class TestRunner():
    def __init__(self):
        self.suite = unittest.TestSuite()
        self.addAllTestCases()
    
    def addAllTestCases(self):
        self.addTestCase(test_action_handlers.AddItemsActionHandlerTest)
        self.addTestCase(test_action_handlers.EditItemsActionHandlerTest)
        self.addTestCase(test_action_handlers.RebuildThumbnailActionHandlerTest)
        self.addTestCase(test_action_handlers.DeleteItemActionHandlerTest)
        self.addTestCase(test_action_handlers.OpenItemActionHandlerTest)
        
        self.addTestCase(test_items_integrity.CheckItemIntegrityTest)
        self.addTestCase(test_items_integrity.FixItemIntegrityTest)
        
        self.addTestCase(test_memento.ItemSerializationSimpleTest)
        self.addTestCase(test_memento.ItemSerializationTest)
        
        self.addTestCase(test_repo_mgr.GetItemTest)
        self.addTestCase(test_repo_mgr.DeleteItemTest)
        self.addTestCase(test_repo_mgr.SaveNewItemTest)
        self.addTestCase(test_repo_mgr.UpdateItemTest)
        
        self.addTestCase(test_worker_threads.DeleteGroupOfItemsThreadTest)
        
        self.addTestCase(test_helpers.IsNoneOrEmptyTest)
        
        
    def addTestCase(self, testCaseCls):
        self.suite.addTests(unittest.TestLoader().loadTestsFromTestCase(testCaseCls))
        
        
    def runAllTests(self):
        unittest.TextTestRunner(verbosity=2).run(self.suite)



def runTestsFromList():
    testRunner = TestRunner()
    testRunner.runAllTests()

def discoverAndRunAllTests():
    loader = unittest.TestLoader()
    try:
        tests = loader.discover(os.path.join(dirAbsPath, ".."))
        testRunner = unittest.runner.TextTestRunner(verbosity=2)
    except AttributeError:
        raise TestsDiscoverIsNotAvailableError()
    testRunner.run(tests)

if __name__ == '__main__':
    print("Current dir is " + os.path.abspath("."))
    
    fileAbsPath = os.path.abspath(__file__)
    dirAbsPath = os.path.dirname(fileAbsPath)
    print("Directory of runtests.py is " + dirAbsPath)
    
    try:
        print("Trying to discover and run all tests...")
        discoverAndRunAllTests()
    except TestsDiscoverIsNotAvailableError:
        print("Tests discovering failed (perhaps you have old python version <= 3.1")
        print("Running all tests from predefined list.")
        runTestsFromList()
    finally:
        print("Done")

    
    
    

    
