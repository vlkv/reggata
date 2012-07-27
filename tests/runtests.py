import unittest
import helpers_test
import repo_mgr_test
import worker_threads_test
import tests_context
import sys
import memento_tests


class TestRunner():
    
    def __init__(self):
        self.suite = unittest.TestSuite()
        self.addAllTestCases()
    
    def addAllTestCases(self):
        self.addTestCase(memento_tests.ItemSerializationSimpleTest)
        self.addTestCase(memento_tests.ItemSerializationTest)
        
        self.addTestCase(helpers_test.IsNoneOrEmptyTest)
        
        self.addTestCase(repo_mgr_test.GetItemTest)
        self.addTestCase(repo_mgr_test.DeleteItemTest)
        self.addTestCase(repo_mgr_test.SaveNewItemTest)
        self.addTestCase(repo_mgr_test.UpdateItemTest)
        
        self.addTestCase(worker_threads_test.DeleteGroupOfItemsThreadTest)

    def addTestCase(self, testCaseCls):
        self.suite.addTests(unittest.TestLoader().loadTestsFromTestCase(testCaseCls))
        
    def runAllTests(self):
        unittest.TextTestRunner(verbosity=2).run(self.suite)



if __name__ == '__main__':
    # sys.argv[0] contains the name of the executing script
    if (len(sys.argv) >= 2):
        tests_context.TEST_REPO_BASE_PATH = sys.argv[1]
    if (len(sys.argv) >= 3):
        tests_context.COPY_OF_TEST_REPO_BASE_PATH = sys.argv[2]

    testRunner = TestRunner()
    testRunner.runAllTests()

    
    
    

    
