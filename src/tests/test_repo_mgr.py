import unittest
from tests.abstract_test_cases import AbstractTestCaseWithRepoAndSingleUOW,\
    AbstractTestCaseWithRepo
from tests.tests_context import COPY_OF_TEST_REPO_BASE_PATH, itemWithFile, nonExistingItem,\
    itemWithTagsAndFields, itemWithoutFile, itemWithErrorFileNotFound, itemWithErrorHashMismatch,\
    itemWithErrorFileNotFoundNo2, itemId_1
from data.repo_mgr import *
from data.commands import *
from errors import *
from data import db_schema
from data.integrity_fixer import IntegrityFixerFactory, FileNotFoundFixer, FileHashMismatchFixer



class GetItemTest(AbstractTestCaseWithRepoAndSingleUOW):
    def test_getExistingItem(self):
        item = self.uow.executeCommand(GetExpungedItemCommand(itemWithFile.id))
        self.assertEqual(item.title, itemWithFile.title)
        
    def test_getNonExistingItem(self):
        cmd = GetExpungedItemCommand(nonExistingItem.id)
        self.assertRaises(NotFoundError, self.uow.executeCommand, (cmd))
        
    def test_passBadIdToGetItem(self):
        cmd = GetExpungedItemCommand("This str is NOT a valid item id!")
        self.assertRaises(NotFoundError, self.uow.executeCommand, (cmd))


class SaveNewItemTest(AbstractTestCaseWithRepo):
    
    def test_saveNewMinimalItem(self):
        # "Minimal item" here means that this item has no data references, tags or fields
        item = Item("user", "Minimal Item")
        try:
            uow = self.repo.createUnitOfWork()
            cmd = SaveNewItemCommand(item)
            self.savedItemId = uow.executeCommand(cmd)
        finally:
            uow.close()
            
        try:
            uow = self.repo.createUnitOfWork()
            savedItem = uow.executeCommand(GetExpungedItemCommand(self.savedItemId))
            self.assertEqual(savedItem.title, item.title)

        finally:
            uow.close()
            
    def test_saveNewItemByNonExistentUserLogin(self):
        nonExistentUserLogin = "NonExistentUserLogin" 
        item = Item(nonExistentUserLogin, "Item's title")
        try:
            uow = self.repo.createUnitOfWork()
            cmd = SaveNewItemCommand(item)
            self.assertRaises(AccessError, uow.executeCommand, (cmd))
            
        finally:
            uow.close()
            
    def test_saveNewItemByNullUserLogin(self):
        userLogin = None
        item = Item(userLogin, "Item's title")
        try:
            uow = self.repo.createUnitOfWork()
            cmd = SaveNewItemCommand(item)
            self.assertRaises(AccessError, uow.executeCommand, (cmd))
        finally:
            uow.close()
            
    def test_saveNewItemByEmptyUserLogin(self):
        userLogin = ""
        item = Item(userLogin, "Item's title")
        try:
            uow = self.repo.createUnitOfWork()
            cmd = SaveNewItemCommand(item)
            self.assertRaises(AccessError, uow.executeCommand, (cmd))
        finally:
            uow.close()

    
    def test_saveNewItemWithFileOutsideRepo(self):
        '''
            User wants to add an external file into the repo. File is copied to the repo.
        '''
        item = Item("user", "Item's title")
        self.srcAbsPath = os.path.abspath(os.path.join(self.repo.base_path, "..", "tmp", "file.txt"))
        self.dstRelPath = os.path.join("dir1", "dir2", "dir3", "newFile.txt")
        try:
            uow = self.repo.createUnitOfWork()
            cmd = SaveNewItemCommand(item, self.srcAbsPath, self.dstRelPath)
            self.savedItemId = uow.executeCommand(cmd)
        finally:
            uow.close()
            
        try:
            uow = self.repo.createUnitOfWork()
            savedItem = uow.executeCommand(GetExpungedItemCommand(self.savedItemId))
            self.assertEqual(savedItem.title, item.title)
            
            self.assertIsNotNone(savedItem.data_ref)
            self.assertEqual(savedItem.data_ref.url_raw, to_db_format(self.dstRelPath))
            self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, savedItem.data_ref.url)))
            
            self.assertTrue(os.path.exists(self.srcAbsPath))
        finally:
            uow.close()
            
    
    def test_saveNewItemWithFileInsideRepo(self):
        '''
            There is an untracked file inside the repo tree. User wants to add such file 
        into the repo to make it a stored file. File is not copied, because it is alredy in 
        the repo tree. It's essential that srcAbsPath and dstRelPath point to the same file.
        '''
        item = Item("user", "Item's title")
        self.srcAbsPath = os.path.abspath(os.path.join(
            self.repo.base_path, "this", "is", "untracked", "file.txt"))
        self.dstRelPath = os.path.join("this", "is", "untracked", "file.txt")
        try:
            uow = self.repo.createUnitOfWork()
            cmd = SaveNewItemCommand(item, self.srcAbsPath, self.dstRelPath)
            self.savedItemId = uow.executeCommand(cmd)
        finally:
            uow.close()
            
        try:
            uow = self.repo.createUnitOfWork()
            savedItem = uow.executeCommand(GetExpungedItemCommand(self.savedItemId))
            self.assertEqual(savedItem.title, item.title)
            
            self.assertIsNotNone(savedItem.data_ref)
            self.assertEqual(savedItem.data_ref.url_raw, to_db_format(self.dstRelPath))
            self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, 
                                                        savedItem.data_ref.url)))
        finally:
            uow.close()
            
    def test_saveNewItemWithACopyOfAStoredFileInRepo(self):
        '''
            User wants to add a copy of a stored file from the repo into the same repo 
        but to the another location. The copy of the original file will be attached 
        to the new Item object.
        '''
        item = Item("user", "Item's title")
        self.srcAbsPath = os.path.abspath(os.path.join(
            self.repo.base_path, "lyrics", "led_zeppelin", "stairway_to_heaven.txt"))
        self.dstRelPath = os.path.join("dir1", "dir2", "dir3", "copy_of_stairway_to_heaven.txt")
        try:
            uow = self.repo.createUnitOfWork()
            cmd = SaveNewItemCommand(item, self.srcAbsPath, self.dstRelPath)
            self.savedItemId = uow.executeCommand(cmd)
        finally:
            uow.close()
            
        try:
            uow = self.repo.createUnitOfWork()
            savedItem = uow.executeCommand(GetExpungedItemCommand(self.savedItemId))
            self.assertEqual(savedItem.title, item.title)
            
            self.assertIsNotNone(savedItem.data_ref)
            self.assertEqual(savedItem.data_ref.url_raw, to_db_format(self.dstRelPath))
            self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, 
                                                        savedItem.data_ref.url)))
            self.assertTrue(os.path.exists(self.srcAbsPath))
        finally:
            uow.close()
            
    def test_saveNewItemWithTags(self):
        userLogin = "user"
        item = Item(userLogin, "Item with tags")
        
        tagNameThatExistsInRepo = "Lyrics"
        tagNameNew = "No items in test repo with such Tag!"
        
        item.add_tag(tagNameThatExistsInRepo, userLogin)
        item.add_tag(tagNameNew, userLogin)
        
        try:
            uow = self.repo.createUnitOfWork()
            cmd = SaveNewItemCommand(item)
            savedItemId = uow.executeCommand(cmd)
        finally:
            uow.close()
            
        savedItem = self.getExistingItem(savedItemId)
        self.assertEqual(savedItem.title, item.title)
        self.assertTrue(savedItem.has_tag(tagNameThatExistsInRepo))
        self.assertTrue(savedItem.has_tag(tagNameNew))
        self.assertEqual(len(savedItem.item_tags), 2)
        
        
    def test_saveNewItemWithFields(self):
        userLogin = "user"
        item = Item(userLogin, "Item with fields")
        
        fieldOne = ("Year", 2012)
        fieldTwo = ("No items in test repo with such Field!", "Some value")
        
        item.set_field_value(fieldOne[0], fieldOne[1], userLogin)
        item.set_field_value(fieldTwo[0], fieldTwo[1], userLogin)
        
        try:
            uow = self.repo.createUnitOfWork()
            cmd = SaveNewItemCommand(item)
            savedItemId = uow.executeCommand(cmd)
        finally:
            uow.close()
            
        savedItem = self.getExistingItem(savedItemId)
        self.assertEqual(savedItem.title, item.title)
        self.assertTrue(savedItem.has_field(fieldOne[0], fieldOne[1]))
        self.assertTrue(savedItem.has_field(fieldTwo[0], fieldTwo[1]))
        self.assertEqual(len(savedItem.item_fields), 2)
        

class DeleteItemTest(AbstractTestCaseWithRepo):
    def test_deleteExistingItemWithExistingPhysicalFileByOwner(self):
        userThatDeletesItem = itemWithFile.ownerUserLogin
        try:
            uow = self.repo.createUnitOfWork()
            itemBeforeDelete = uow.executeCommand(GetExpungedItemCommand(itemWithFile.id))
            
            cmd = DeleteItemCommand(itemWithFile.id, userThatDeletesItem, 
                                    delete_physical_file=True)
            uow.executeCommand(cmd)
        finally:
            uow.close()
        
        try:
            uow = self.repo.createUnitOfWork()
            deletedItem = uow.executeCommand(GetExpungedItemCommand(itemWithFile.id))
            self.assertFalse(deletedItem.alive)
            self.assertIsNone(deletedItem.data_ref)
            
            #NOTE that tags/fields collections are not cleared, as you might expect
            self.assertTrue(len(deletedItem.item_tags) >= 0)
            self.assertTrue(len(deletedItem.item_fields) >= 0)

        finally:
            uow.close()
        self.assertFalse(os.path.exists(os.path.join(COPY_OF_TEST_REPO_BASE_PATH, itemWithFile.relFilePath)))
        





class UpdateItemTest(AbstractTestCaseWithRepo):
    
    def test_updateItemTitleByOwner(self):
        item = self.getExistingItem(itemWithFile.id)
        self.assertEqual(item.title, itemWithFile.title)
            
        #Change item's title
        newItemTitle = "ABCDEF"
        self.assertNotEqual(item.title, newItemTitle, 
                            "You should change item's title to some different value.") 
        item.title = newItemTitle
            
        self.updateExistingItem(item, item.user_login)
            
        #Get an item from repo again and check it's title
        item = self.getExistingItem(itemWithFile.id)
        self.assertEqual(item.title, newItemTitle)
        
        

    def test_updateItemTagsByOwner(self):
        userLogin = "user"
        item = self.getExistingItem(itemWithTagsAndFields.id)
        self.assertEqual(item.title, itemWithTagsAndFields.title)
        self.assertEqual(len(item.item_tags), len(itemWithTagsAndFields.tags))
        self.assertEqual(len(itemWithTagsAndFields.tags), 2)
        
        #Remove one existing tag
        tagNameToRemove = "RHCP"
        self.assertTrue(item.has_tag(tagNameToRemove))
        self.assertTrue(item.remove_tag(tagNameToRemove))
        
        #Add one new tag
        tagNameToAdd = "TagNameToAdd"
        self.assertNotEqual(tagNameToRemove, tagNameToAdd)
        self.assertFalse(item.has_tag(tagNameToAdd))
        item.add_tag(tagNameToAdd, userLogin)
        
        self.updateExistingItem(item, item.user_login)
        
        item = self.getExistingItem(itemWithTagsAndFields.id)
        self.assertFalse(item.has_tag(tagNameToRemove))
        self.assertTrue(item.has_tag(tagNameToAdd))
        self.assertTrue(item.has_tag("Lyrics"))
        self.assertEqual(len(item.item_tags), 2)
               
        
    def test_updateItemFieldsByOwner(self):
        userLogin = itemWithTagsAndFields.ownerUserLogin
        
        item = self.getExistingItem(itemWithTagsAndFields.id)
        self.assertEqual(item.title, itemWithTagsAndFields.title)
        self.assertEqual(len(item.item_fields), len(itemWithTagsAndFields.fields))
        self.assertEqual(len(itemWithTagsAndFields.fields), 4)
        
        #Remove one existing field
        fieldNameToRemove = "Year"
        self.assertTrue(item.has_field(fieldNameToRemove, 1991))
        self.assertTrue(item.remove_field(fieldNameToRemove))
        
        #Add one new field
        fieldToAdd = ("FieldNameToAdd", "Some value")
        self.assertFalse(item.has_field(fieldToAdd[0]))
        item.set_field_value(fieldToAdd[0], fieldToAdd[1], userLogin)
        
        #Edit one existing field
        fieldToEdit = ("Notes", "Some new notes")
        self.assertTrue(item.has_field(fieldToEdit[0]))
        self.assertFalse(item.has_field(fieldToEdit[0], fieldToEdit[1]))
        item.set_field_value(fieldToEdit[0], fieldToEdit[1], userLogin)
        
        self.updateExistingItem(item, item.user_login)
        
        item = self.getExistingItem(itemWithTagsAndFields.id)
        self.assertFalse(item.has_field(fieldNameToRemove))
        self.assertTrue(item.has_field(fieldToAdd[0], fieldToAdd[1]))
        self.assertTrue(item.has_field(fieldToEdit[0], fieldToEdit[1]))
        self.assertTrue(item.has_field("Rating", 5))
        self.assertTrue(item.has_field("Albom", "Blood Sugar Sex Magik"))
        self.assertEqual(len(item.item_fields), 4)
        

    def test_addFileToItemWithoutFile(self):
        #TODO: Add HistoryRec checking
        
        # Referenced file for new DataRef will be from the outside of the repo
        item = self.getExistingItem(itemWithoutFile.id)
        self.assertEqual(item.title, itemWithoutFile.title)
        self.assertIsNone(item.data_ref)
        self.assertFalse(os.path.exists(os.path.join(self.repo.base_path, "file.txt")))
        
        # Link file with the item
        srcAbsPath = os.path.abspath(os.path.join(self.repo.base_path, "..", "tmp", "file.txt"))
        item.data_ref = DataRef(DataRef.FILE, srcAbsPath)
        
        self.updateExistingItem(item, item.user_login)
            
        item = self.getExistingItem(itemWithoutFile.id)
        self.assertEqual(item.title, itemWithoutFile.title)
        self.assertIsNotNone(item.data_ref)
        self.assertEqual(item.data_ref.url, "file.txt")
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, "file.txt")))
        
        
    def test_addFileToItemWithoutFileWithDestinationInsideRepo(self):
        #TODO: Add HistoryRec checking
        
        # Referenced file for new DataRef will be from the outside of the repo
        # We will specify the destination path in the repo - where to put the file
        
        item = self.getExistingItem(itemWithoutFile.id)
        self.assertEqual(item.title, itemWithoutFile.title)
        self.assertIsNone(item.data_ref)
        self.assertFalse(os.path.exists(os.path.join(self.repo.base_path, "dir1", "dir2", "file.txt")))
        
        # Link file with the item
        srcAbsPath = os.path.abspath(os.path.join(self.repo.base_path, "..", "tmp", "file.txt"))
        item.data_ref = DataRef(DataRef.FILE, srcAbsPath)
        item.data_ref.dstRelPath = os.path.join("dir1", "dir2", "copied_file.txt")
        
        self.updateExistingItem(item, item.user_login)
            
        item = self.getExistingItem(itemWithoutFile.id)
        self.assertEqual(item.title, itemWithoutFile.title)
        self.assertIsNotNone(item.data_ref)
        self.assertEqual(to_db_format(item.data_ref.url), "dir1/dir2/copied_file.txt")
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, "dir1", "dir2", "copied_file.txt")))
        self.assertFalse(os.path.isdir(os.path.join(self.repo.base_path, "dir1", "dir2", "copied_file.txt")))
    
    
    def test_moveFileOfItemToAnotherLocationWithinRepo(self):
        item = self.getExistingItem(itemWithTagsAndFields.id)
        self.assertEqual(item.title, itemWithTagsAndFields.title)
        self.assertIsNotNone(item.data_ref)
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, item.data_ref.url)))
        
        # Move linked file to another location within the repository
        path = ["new", "location", "for", "file", "I Could Have Lied.txt"]
        item.data_ref.dstRelPath = os.path.join(*path)
        
        self.updateExistingItem(item, item.user_login)
            
        item = self.getExistingItem(itemWithTagsAndFields.id)
        self.assertEqual(item.title, itemWithTagsAndFields.title)
        self.assertIsNotNone(item.data_ref)
        self.assertEqual(to_db_format(item.data_ref.url), "new/location/for/file/I Could Have Lied.txt")
        self.assertFalse(os.path.isdir(os.path.join(self.repo.base_path, *path)))
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, *path)))
    
    def test_moveFileOfItemToAnotherLocationWithinRepoAndRename(self):
        item = self.getExistingItem(itemWithTagsAndFields.id)
        self.assertEqual(item.title, itemWithTagsAndFields.title)
        self.assertIsNotNone(item.data_ref)
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, item.data_ref.url)))
        
        # Move linked file to another location within the repository
        # NOTE: File will be not only moved, but also renamed
        path = ["new", "location", "for", "file", "could_have_lied_lyrics.txt"]
        item.data_ref.dstRelPath = os.path.join(*path)
        
        self.updateExistingItem(item, item.user_login)
            
        item = self.getExistingItem(itemWithTagsAndFields.id)
        self.assertEqual(item.title, itemWithTagsAndFields.title)
        self.assertIsNotNone(item.data_ref)
        self.assertEqual(to_db_format(item.data_ref.url), "new/location/for/file/could_have_lied_lyrics.txt")
        self.assertFalse(os.path.isdir(os.path.join(self.repo.base_path, *path)))
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, *path)))
    
    def test_removeFileFromItem(self):
        item = self.getExistingItem(itemWithTagsAndFields.id)
        self.assertEqual(item.title, itemWithTagsAndFields.title)
        self.assertIsNotNone(item.data_ref)
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, item.data_ref.url)))
        
        item.data_ref = None
        
        self.updateExistingItem(item, item.user_login)
            
        item = self.getExistingItem(itemWithTagsAndFields.id)
        self.assertEqual(item.title, itemWithTagsAndFields.title)
        self.assertIsNone(item.data_ref)
        
        # Physical file should not be deleted
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, itemWithTagsAndFields.relFilePath)))
        #DataRef should not be deleted after this operation
        dataRef = self.getDataRef(itemWithTagsAndFields.relFilePath)
        self.assertIsNotNone(dataRef)
        

    def test_replaceFileOfItemWithAnotherOuterFile(self):
        # File of new DataRef will be from the outside of the repo
        item = self.getExistingItem(itemWithTagsAndFields.id)
        self.assertIsNotNone(item)
        
        # Link file with the item
        url = os.path.abspath(os.path.join(self.repo.base_path, "..", "tmp", "file.txt"))
        item.data_ref = DataRef(DataRef.FILE, url)
        
        self.updateExistingItem(item, item.user_login)
        
        item = self.getExistingItem(itemWithTagsAndFields.id)
        self.assertEqual(item.title, itemWithTagsAndFields.title)
        self.assertIsNotNone(item.data_ref)
        self.assertEqual(item.data_ref.url, "file.txt")
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, "file.txt")))
        
        # Old physical file should not be deleted
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, itemWithTagsAndFields.relFilePath)))
        #Old DataRef should not be deleted after this operation
        dataRef = self.getDataRef(itemWithTagsAndFields.relFilePath)
        self.assertIsNotNone(dataRef)
    
    def test_replaceFileOfItemWithAnotherInnerFile(self):
        # File of new DataRef will be from the same repo.
        # But the new file is not a stored file (it has no corresponding DataRef object)
        item = self.getExistingItem(itemWithTagsAndFields.id)
        self.assertIsNotNone(item)
        self.assertIsNotNone(item.data_ref)
        self.assertEqual(to_db_format(item.data_ref.url), itemWithTagsAndFields.relFilePath)
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, item.data_ref.url)))
        
        # Link file with the item
        relUrl = os.path.join("this", "is", "untracked", "file.txt")
        absUrl = os.path.abspath(os.path.join(self.repo.base_path, relUrl))
        self.assertTrue(os.path.exists(absUrl))
        item.data_ref = DataRef(DataRef.FILE, absUrl)
        
        self.updateExistingItem(item, item.user_login)
        
        item = self.getExistingItem(itemWithTagsAndFields.id)
        self.assertEqual(item.title, itemWithTagsAndFields.title)
        self.assertIsNotNone(item.data_ref)
        self.assertEqual(item.data_ref.url, relUrl)
        self.assertTrue(os.path.exists(absUrl))
        
        # Old physical file should not be deleted
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, itemWithTagsAndFields.relFilePath)))
        #Old DataRef should not be deleted after this operation
        dataRef = self.getDataRef(itemWithTagsAndFields.relFilePath)
        self.assertIsNotNone(dataRef)
    
    def test_replaceFileOfItemWithAnotherInnerStoredFile(self):
        # File of new DataRef will be from the same repo, and it will be 
        # a stored file (linked with some other item)
        item = self.getExistingItem(itemWithTagsAndFields.id)
        self.assertIsNotNone(item)
        self.assertIsNotNone(item.data_ref)
        self.assertEqual(to_db_format(item.data_ref.url), itemWithTagsAndFields.relFilePath)
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, item.data_ref.url)))
        
        # Link file with the item
        relUrl = itemWithFile.relFilePath
        absUrl = os.path.abspath(os.path.join(self.repo.base_path, relUrl))
        self.assertTrue(os.path.exists(absUrl))
        item.data_ref = DataRef(DataRef.FILE, absUrl)
        
        self.updateExistingItem(item, item.user_login)
        
        item = self.getExistingItem(itemWithTagsAndFields.id)
        self.assertEqual(item.title, itemWithTagsAndFields.title)
        self.assertIsNotNone(item.data_ref)
        self.assertEqual(item.data_ref.url, relUrl)
        self.assertTrue(os.path.exists(absUrl))
        
        #Two different items now share same DataRef
        otherItem = self.getExistingItem(itemWithFile.id)
        self.assertIsNotNone(otherItem.data_ref)
        self.assertEquals(item.data_ref.id, otherItem.data_ref.id)
        
        # Old physical file should not be deleted
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, itemWithTagsAndFields.relFilePath)))
        #Old DataRef should not be deleted after this operation
        dataRef = self.getDataRef(itemWithTagsAndFields.relFilePath)
        self.assertIsNotNone(dataRef)

    
        
    #def test_addTagsToItemByNotOwnerUser(self):
        #TODO implement test
    #    pass
    
    #def test_removeTagsFromItemByNotOwnerUser(self):
        #TODO implement test
    #    pass
    
    
    
class CheckItemIntegrityTest(AbstractTestCaseWithRepo):
    
    def test_checkItemWithoutErrors(self):        
        item = self.getExistingItem(itemWithFile.id)
        uow = self.repo.createUnitOfWork()
        try:
            cmd = CheckItemIntegrityCommand(item, self.repo.base_path)
            errors = uow.executeCommand(cmd)
            self.assertTrue(len(errors) == 0)
        finally:
            uow.close()
    
    
    def test_checkItemWithErrorFileNotFound(self):
        item = self.getExistingItem(itemWithErrorFileNotFound.id)
        uow = self.repo.createUnitOfWork()
        try:
            cmd = CheckItemIntegrityCommand(item, self.repo.base_path)
            errors = uow.executeCommand(cmd)
            self.assertTrue(len(errors) == 1)
            self.assertTrue(db_schema.Item.ERROR_FILE_NOT_FOUND in errors)
        finally:
            uow.close()
            
    def test_checkItemWithErrorFileHashMismatch(self):
        item = self.getExistingItem(itemWithErrorHashMismatch.id)
        uow = self.repo.createUnitOfWork()
        try:
            cmd = CheckItemIntegrityCommand(item, self.repo.base_path)
            errors = uow.executeCommand(cmd)
            self.assertTrue(len(errors) == 1)
            self.assertTrue(db_schema.Item.ERROR_FILE_HASH_MISMATCH in errors)
        finally:
            uow.close()


class FixItemIntegrityTest(AbstractTestCaseWithRepo):
    
    def test_fixItemWithErrorFileNotFound_TryFind(self):
        '''
            Fixer should find file in the repo in a different location. And a new 
        DataRef object will be created for it.
        '''
        item = self.getExistingItem(itemWithErrorFileNotFound.id)
        originalDataRefId = item.data_ref.id
        uow = self.repo.createUnitOfWork()
        try:
            itemsLock = QtCore.QReadWriteLock()
            fixer = IntegrityFixerFactory.createFixer(Item.ERROR_FILE_NOT_FOUND, 
                                              FileNotFoundFixer.TRY_FIND, 
                                              uow, self.repo.base_path, itemsLock)
            result = fixer.fix_error(item, itemWithErrorFileNotFound.ownerUserLogin)
            uow.session.commit()
            
            self.assertTrue(result)
            
        finally:
            uow.close()
            
        fixedItem = self.getExistingItem(itemWithErrorFileNotFound.id)
        fileAbsPath = os.path.join(self.repo.base_path, fixedItem.data_ref.url)
        self.assertTrue(os.path.exists(fileAbsPath))
        
        self.assertEquals(originalDataRefId, fixedItem.data_ref.id, "DataRef object should be still the same")
        
        
    def test_fixItemWithErrorFileNotFound_TryFind_No2(self):
        '''
            This test is a little different from test_fixItemWithErrorFileNotFound_TryFind.
        Fixer should find in the repo an existing DataRef object with the same matching hash.
        '''
        item = self.getExistingItem(itemWithErrorFileNotFoundNo2.id)
        originalDataRefId = item.data_ref.id
        uow = self.repo.createUnitOfWork()
        try:
            itemsLock = QtCore.QReadWriteLock()
            fixer = IntegrityFixerFactory.createFixer(Item.ERROR_FILE_NOT_FOUND, 
                                              FileNotFoundFixer.TRY_FIND, 
                                              uow, self.repo.base_path, itemsLock)
            result = fixer.fix_error(item, itemWithErrorFileNotFoundNo2.ownerUserLogin)
            uow.session.commit()
            
            self.assertTrue(result)
            
        finally:
            uow.close()
            
        fixedItem = self.getExistingItem(itemWithErrorFileNotFoundNo2.id)
        fileAbsPath = os.path.join(self.repo.base_path, fixedItem.data_ref.url)
        self.assertTrue(os.path.exists(fileAbsPath))
        
        originalDataRef = self.getDataRefById(originalDataRefId)
        self.assertIsNone(originalDataRef, "Original DataRef object should be deleted from database")
        
        anotherItem = self.getExistingItem(itemId_1.id)
        self.assertEquals(fixedItem.data_ref.id, anotherItem.data_ref.id, 
            "Now two different items reference to the same DataRef object")
        
    def test_fixItemWithErrorFileNotFound_Delete(self):
        '''
            Fixer should just delete Item's reference to the missed file and delete corresponding 
        DataRef object from database.
        '''
        item = self.getExistingItem(itemWithErrorFileNotFound.id)
        originalDataRefId = item.data_ref.id
        uow = self.repo.createUnitOfWork()
        try:
            itemsLock = QtCore.QReadWriteLock()
            fixer = IntegrityFixerFactory.createFixer(Item.ERROR_FILE_NOT_FOUND, 
                                              FileNotFoundFixer.DELETE, 
                                              uow, self.repo.base_path, itemsLock)
            result = fixer.fix_error(item, itemWithErrorFileNotFound.ownerUserLogin)
            uow.session.commit()
            
            self.assertTrue(result)
            
        finally:
            uow.close()
            
        fixedItem = self.getExistingItem(itemWithErrorFileNotFound.id)
        self.assertIsNone(fixedItem.data_ref, "Item has no references to files now")
        
        originalDataRef = self.getDataRefById(originalDataRefId)
        self.assertIsNone(originalDataRef, "Original DataRef object should be deleted from database")
            
            
    def test_fixItemWithErrorHashMismatch_UpdateHash(self):
        item = self.getExistingItem(itemWithErrorHashMismatch.id)
        originalDataRefId = item.data_ref.id
        originalFileHash = item.data_ref.hash
        originalFilePath = item.data_ref.url_raw
        uow = self.repo.createUnitOfWork()
        try:
            itemsLock = QtCore.QReadWriteLock()
            fixer = IntegrityFixerFactory.createFixer(Item.ERROR_FILE_HASH_MISMATCH, 
                                              FileHashMismatchFixer.UPDATE_HASH, 
                                              uow, self.repo.base_path, itemsLock)
            result = fixer.fix_error(item, itemWithErrorHashMismatch.ownerUserLogin)
            uow.session.commit()
            
            self.assertTrue(result)
            
        finally:
            uow.close()
        
        fixedItem = self.getExistingItem(itemWithErrorHashMismatch.id)
        self.assertNotEquals(originalFileHash, fixedItem.data_ref.hash, 
            "File hash should be different now")
        
        self.assertEquals(originalDataRefId, fixedItem.data_ref.id, 
            "DataRef object should be still the same")
        
        self.assertEquals(originalFilePath, fixedItem.data_ref.url_raw, 
            "File path should be still the same")
            
            
    def test_fixItemWithErrorHashMismatch_TryFind(self):
        item = self.getExistingItem(itemWithErrorHashMismatch.id)
        originalDataRefId = item.data_ref.id
        originalDataRefUrl = item.data_ref.url_raw
        originalFileHash = item.data_ref.hash
        uow = self.repo.createUnitOfWork()
        try:
            itemsLock = QtCore.QReadWriteLock()
            fixer = IntegrityFixerFactory.createFixer(Item.ERROR_FILE_HASH_MISMATCH, 
                                              FileHashMismatchFixer.TRY_FIND_FILE, 
                                              uow, self.repo.base_path, itemsLock)
            result = fixer.fix_error(item, itemWithErrorHashMismatch.ownerUserLogin)
            uow.session.commit()
            
            self.assertTrue(result)
            
        finally:
            uow.close()
        
        fixedItem = self.getExistingItem(itemWithErrorHashMismatch.id)
        fileAbsPath = os.path.join(self.repo.base_path, fixedItem.data_ref.url)
        self.assertTrue(os.path.exists(fileAbsPath))
        
        originalDataRef = self.getDataRefById(originalDataRefId)
        self.assertIsNone(originalDataRef, 
            "Original DataRef object should be deleted")
        
        self.assertNotEquals(originalDataRefUrl, fixedItem.data_ref.url_raw, 
            "Item should reference to a different file now")
        
        self.assertEquals(originalFileHash, fixedItem.data_ref.hash,
            "File hash should be still the same")
        
            