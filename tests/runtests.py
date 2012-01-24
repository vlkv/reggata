import unittest
import helpers_test
import repo_mgr_test
import os


if __name__ == '__main__':

    #TODO: pass path to testrepo.rgt as a command line argument    
    print(os.path.abspath("."))
    
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(helpers_test.IsNoneOrEmptyTest))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(repo_mgr_test.GetItemTest))
    unittest.TextTestRunner(verbosity=2).run(suite)
    