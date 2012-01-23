import unittest
import helpers


class IsNoneOrEmptyTest(unittest.TestCase):

    def test_isNoneOrEmpty_empty(self):
        emptyStr = ""
        self.assertTrue(helpers.is_none_or_empty(emptyStr))
        
    def test_isNoneOrEmpty_none(self):
        noneObj = None
        self.assertTrue(helpers.is_none_or_empty(noneObj))
        
    def test_isNoneOrEmpty_nonEmptyStr(self):
        nonEmptyStr = "Reggata"
        self.assertFalse(helpers.is_none_or_empty(nonEmptyStr))
        
    def test_isNoneOrEmpty_nonStrObj(self):
        listObj = [1, 2, 3]
        self.assertRaises(TypeError, helpers.is_none_or_empty, (listObj))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()