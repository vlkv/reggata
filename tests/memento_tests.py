# -*- coding: utf-8 -*-
'''
Created on 27.07.2012

@author: vlkv
'''

import unittest
import db_schema
import memento
from tests_context import *
import os
from abstract_test_cases import AbstractTestCaseWithRepo

class ItemSerializationSimpleTest(unittest.TestCase):

    def test_saveItemState(self):
        item = db_schema.Item(user_login="user", title="The Title")
        jsonStr = memento.Encoder().encode(item)
        expectedJsonStr = '''{
    "__class__": "Item", 
    "__module__": "db_schema", 
    "id": null, 
    "title": "The Title"
}'''
        self.assertEqual(jsonStr, expectedJsonStr)
        
    def test_restoreItemState(self):
        jsonStr = '''{
    "__class__": "Item", 
    "__module__": "db_schema", 
    "id": null, 
    "title": "The Title"
}'''
        item = memento.Decoder().decode(jsonStr)
        self.assertTrue(isinstance(item, db_schema.Item))
        self.assertEquals(item.title, "The Title")
        self.assertIsNone(item.id)
        

class ItemSerializationTest(AbstractTestCaseWithRepo):

    def test_saveExistingItemFromRepo(self):
        item = self.getExistingItem(itemWithTagsAndFields.id)
        self.assertEqual(item.title, itemWithTagsAndFields.title)
        self.assertIsNotNone(item.data_ref)
        
        jsonStr = memento.Encoder().encode(item)
        expectedJsonStr = '{\n    "__class__": "Item", \n    "__module__": "db_schema", \n    "id": 5, \n    "title": "I Could Have Lied.txt"\n}'
        self.assertEquals(jsonStr, expectedJsonStr)
        

if __name__ == "__main__":
    unittest.main()
    