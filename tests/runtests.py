import unittest
import helpers_test
import repo_mgr_test
import worker_threads_test
import tests_context
import sys
import memento_tests

def addTestCase(suite, testCase):
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(testCase))

if __name__ == '__main__':
    # sys.argv[0] contains the name of the executing script
    if (len(sys.argv) >= 2):
        tests_context.TEST_REPO_BASE_PATH = sys.argv[1]
    if (len(sys.argv) >= 3):
        tests_context.COPY_OF_TEST_REPO_BASE_PATH = sys.argv[2]

    suite = unittest.TestSuite()
    
    addTestCase(suite, helpers_test.IsNoneOrEmptyTest)
    
    addTestCase(suite, repo_mgr_test.GetItemTest)
    addTestCase(suite, repo_mgr_test.DeleteItemTest)
    addTestCase(suite, repo_mgr_test.SaveNewItemTest)
    addTestCase(suite, repo_mgr_test.UpdateItemTest)
    
    addTestCase(suite, worker_threads_test.DeleteGroupOfItemsThreadTest)
    
    addTestCase(suite, memento_tests.ItemSerializationSimpleTest)

    unittest.TextTestRunner(verbosity=2).run(suite)
