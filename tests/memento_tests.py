# -*- coding: utf-8 -*-
'''
Created on 27.07.2012

@author: vlkv
'''

import unittest
import db_schema
import memento

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
        
        

if __name__ == "__main__":
    unittest.main()
    