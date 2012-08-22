import unittest
import os

if __name__ == '__main__':
    
    print("Current dir is " + os.path.abspath("."))
    
    fileAbsPath = os.path.abspath(__file__)
    dirAbsPath = os.path.dirname(fileAbsPath)
    print("Directory of runtests.py is " + dirAbsPath)

    loader = unittest.TestLoader()
    tests = loader.discover(os.path.join(dirAbsPath, ".."))
    testRunner = unittest.runner.TextTestRunner(verbosity=2)
    testRunner.run(tests)


    
    
    

    
