# -*- coding: utf-8 -*-
'''
Created on 27.07.2012
@author: vlkv
'''
import unittest
import datetime
from reggata.data.db_schema import Item
import reggata.memento as memento
from reggata.tests.tests_context import itemWithTagsAndFields
from reggata.tests.abstract_test_cases import AbstractTestCaseWithRepo


class ItemSerializationSimpleTest(unittest.TestCase):

    simpleItemState = '''{
    "__class__": "Item",
    "__module__": "reggata.data.db_schema",
    "__version__": 1,
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
        item = Item(user_login="user", title="The Title")
        item.date_created = datetime.datetime(2012, 7, 27, 23, 14, 14, 680387)
        jsonStr = memento.Encoder().encode(item)
        expectedJsonStr = ItemSerializationSimpleTest.simpleItemState
        self.assertEqual(jsonStr, expectedJsonStr)

    def test_restoreItemState(self):
        jsonStr = ItemSerializationSimpleTest.simpleItemState
        item = memento.Decoder().decode(jsonStr)
        self.assertTrue(isinstance(item, Item))
        self.assertIsNone(item.data_ref)
        self.assertEquals(item.date_created, datetime.datetime(2012, 7, 27, 23, 14, 14, 680387))
        self.assertTrue(len(item.item_fields) == 0)
        self.assertTrue(len(item.item_tags) == 0)
        self.assertEquals(item.title, "The Title")
        self.assertEquals(item.user_login, "user")
        self.assertIsNone(item.id)

    # TODO: add test for the case: Item is restored from json state with old version


class ItemSerializationTest(AbstractTestCaseWithRepo):

    def test_saveExistingItemFromRepo(self):
        item = self.getExistingItem(itemWithTagsAndFields.id)
        jsonStr = memento.Encoder().encode(item)

        item2 = memento.Decoder().decode(jsonStr)
        self.assertTrue(isinstance(item2, Item))
        self.assertEquals(item2.title, itemWithTagsAndFields.title)
        self.assertEquals(item2.user_login, itemWithTagsAndFields.ownerUserLogin)
        self.assertEquals(item2.data_ref.url_raw, itemWithTagsAndFields.relFilePath)

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
