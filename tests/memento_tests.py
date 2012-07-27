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
import datetime
from test.test_capi import InstanceMethod

class ItemSerializationSimpleTest(unittest.TestCase):

    simpleItemState = '''{
    "__class__": "Item", 
    "__module__": "db_schema", 
    "data_ref": null, 
    "date_created": {
        "__datetime__": "datetime.datetime(2012, 7, 27, 23, 14, 14, 680387)"
    }, 
    "fields": [], 
    "tags": [], 
    "title": "The Title", 
    "user_login": "user"
}'''

    def test_saveItemState(self):
        item = db_schema.Item(user_login="user", title="The Title")
        item.date_created = datetime.datetime(2012, 7, 27, 23, 14, 14, 680387)
        jsonStr = memento.Encoder().encode(item)
        expectedJsonStr = ItemSerializationSimpleTest.simpleItemState 
        self.assertEqual(jsonStr, expectedJsonStr)
        
    def test_restoreItemState(self):
        jsonStr = ItemSerializationSimpleTest.simpleItemState
        item = memento.Decoder().decode(jsonStr)
        self.assertTrue(isinstance(item, db_schema.Item))
        self.assertIsNone(item.data_ref)
        self.assertEquals(item.date_created, datetime.datetime(2012, 7, 27, 23, 14, 14, 680387))
        self.assertTrue(len(item.item_fields) == 0)
        self.assertTrue(len(item.item_tags) == 0)
        self.assertEquals(item.title, "The Title")
        self.assertEquals(item.user_login, "user")
        self.assertIsNone(item.id)
        

class ItemSerializationTest(AbstractTestCaseWithRepo):

    def test_saveExistingItemFromRepo(self):
        item = self.getExistingItem(itemWithTagsAndFields.id)
        jsonStr = memento.Encoder().encode(item)
        
        item2 = memento.Decoder().decode(jsonStr)
        self.assertTrue(isinstance(item2, db_schema.Item))
        self.assertEquals(item2.title, itemWithTagsAndFields.title)
        self.assertEquals(item2.user_login, itemWithTagsAndFields.ownerUserLogin)
        self.assertEquals(item2.data_ref.url, itemWithTagsAndFields.relFilePath)
        
        self.assertEquals(len(item2.item_tags), len(itemWithTagsAndFields.tags))
        for i in range(len(item2.item_tags)):
            tagName = item2.item_tags[i].tag.name
            self.assertTrue(tagName in itemWithTagsAndFields.tags)
            
        self.assertEquals(len(item2.item_fields), len(itemWithTagsAndFields.fields))
        for i in range(len(item2.item_fields)):
            fieldName = item2.item_fields[i].field.name
            fieldVal = item2.item_fields[i].field_value
            self.assertTrue(fieldName in itemWithTagsAndFields.fields.keys())
            self.assertEquals(fieldVal, str(itemWithTagsAndFields.fields[fieldName]))
        
        # NOTE: There are a number of Item and DataRef properties, 
        # that not checked in this test! Be careful..     
        
        
        

if __name__ == "__main__":
    unittest.main()
    