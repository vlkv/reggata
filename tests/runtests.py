import unittest
import helpers_test
import repo_mgr_test
import tests_context
import sys


if __name__ == '__main__':
    
    # sys.argv[0] contains the name of the executing script
    if (len(sys.argv) >= 2):
        tests_context.TEST_REPO_BASE_PATH = sys.argv[1]
    if (len(sys.argv) >= 3):
        tests_context.COPY_OF_TEST_REPO_BASE_PATH = sys.argv[2]
    
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(helpers_test.IsNoneOrEmptyTest))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(repo_mgr_test.GetItemTest))
    unittest.TextTestRunner(verbosity=2).run(suite)
    