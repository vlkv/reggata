from reggata.tests.abstract_test_cases import AbstractTestCaseWithRepoAndSingleUOW, \
    AbstractTestCaseWithRepo
import reggata.tests.tests_context as context
import reggata.data.db_schema as db
import reggata.data.commands as cmds
import reggata.errors as err
import reggata.helpers as hlp
import os


class GetItemTest(AbstractTestCaseWithRepoAndSingleUOW):
    def test_getExistingItem(self):
        item = self.uow.executeCommand(cmds.GetExpungedItemCommand(context.itemWithFile.id))
        self.assertEqual(item.title, context.itemWithFile.title)

    def test_getNonExistingItem(self):
        cmd = cmds.GetExpungedItemCommand(context.nonExistingItem.id)
        self.assertRaises(err.NotFoundError, self.uow.executeCommand, (cmd))

    def test_passBadIdToGetItem(self):
        cmd = cmds.GetExpungedItemCommand("This str is NOT a valid item id!")
        self.assertRaises(err.NotFoundError, self.uow.executeCommand, (cmd))


class SaveNewItemTest(AbstractTestCaseWithRepo):

    def test_saveNewMinimalItem(self):
        # "Minimal item" here means that this item has no data references, tags or fields
        item = db.Item("user", "Minimal Item")
        try:
            uow = self.repo.createUnitOfWork()
            cmd = cmds.SaveNewItemCommand(item)
            self.savedItemId = uow.executeCommand(cmd)
        finally:
            uow.close()

        try:
            uow = self.repo.createUnitOfWork()
            savedItem = uow.executeCommand(cmds.GetExpungedItemCommand(self.savedItemId))
            self.assertEqual(savedItem.title, item.title)

        finally:
            uow.close()

    def test_saveNewItemByNonExistentUserLogin(self):
        nonExistentUserLogin = "NonExistentUserLogin"
        item = db.Item(nonExistentUserLogin, "Item's title")
        try:
            uow = self.repo.createUnitOfWork()
            cmd = cmds.SaveNewItemCommand(item)
            self.assertRaises(err.AccessError, uow.executeCommand, (cmd))

        finally:
            uow.close()

    def test_saveNewItemByNullUserLogin(self):
        userLogin = None
        item = db.Item(userLogin, "Item's title")
        try:
            uow = self.repo.createUnitOfWork()
            cmd = cmds.SaveNewItemCommand(item)
            self.assertRaises(err.AccessError, uow.executeCommand, (cmd))
        finally:
            uow.close()

    def test_saveNewItemByEmptyUserLogin(self):
        userLogin = ""
        item = db.Item(userLogin, "Item's title")
        try:
            uow = self.repo.createUnitOfWork()
            cmd = cmds.SaveNewItemCommand(item)
            self.assertRaises(err.AccessError, uow.executeCommand, (cmd))
        finally:
            uow.close()


    def test_saveNewItemWithFileOutsideRepo(self):
        '''
            User wants to add an external file into the repo. File is copied to the repo.
        '''
        item = db.Item("user", "Item's title")
        self.srcAbsPath = os.path.abspath(os.path.join(self.repo.base_path, "..", "tmp", "file.txt"))
        self.dstRelPath = os.path.join("dir1", "dir2", "dir3", "newFile.txt")
        try:
            uow = self.repo.createUnitOfWork()
            cmd = cmds.SaveNewItemCommand(item, self.srcAbsPath, self.dstRelPath)
            self.savedItemId = uow.executeCommand(cmd)
        finally:
            uow.close()

        try:
            uow = self.repo.createUnitOfWork()
            savedItem = uow.executeCommand(cmds.GetExpungedItemCommand(self.savedItemId))
            self.assertEqual(savedItem.title, item.title)

            self.assertIsNotNone(savedItem.data_ref)
            self.assertEqual(savedItem.data_ref.url_raw, hlp.to_db_format(self.dstRelPath))
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
        item = db.Item("user", "Item's title")
        self.srcAbsPath = os.path.abspath(os.path.join(
            self.repo.base_path, "this", "is", "untracked", "file.txt"))
        self.dstRelPath = os.path.join("this", "is", "untracked", "file.txt")
        try:
            uow = self.repo.createUnitOfWork()
            cmd = cmds.SaveNewItemCommand(item, self.srcAbsPath, self.dstRelPath)
            self.savedItemId = uow.executeCommand(cmd)
        finally:
            uow.close()

        try:
            uow = self.repo.createUnitOfWork()
            savedItem = uow.executeCommand(cmds.GetExpungedItemCommand(self.savedItemId))
            self.assertEqual(savedItem.title, item.title)

            self.assertIsNotNone(savedItem.data_ref)
            self.assertEqual(savedItem.data_ref.url_raw, hlp.to_db_format(self.dstRelPath))
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
        item = db.Item("user", "Item's title")
        self.srcAbsPath = os.path.abspath(os.path.join(
            self.repo.base_path, "lyrics", "led_zeppelin", "stairway_to_heaven.txt"))
        self.dstRelPath = os.path.join("dir1", "dir2", "dir3", "copy_of_stairway_to_heaven.txt")
        try:
            uow = self.repo.createUnitOfWork()
            cmd = cmds.SaveNewItemCommand(item, self.srcAbsPath, self.dstRelPath)
            self.savedItemId = uow.executeCommand(cmd)
        finally:
            uow.close()

        try:
            uow = self.repo.createUnitOfWork()
            savedItem = uow.executeCommand(cmds.GetExpungedItemCommand(self.savedItemId))
            self.assertEqual(savedItem.title, item.title)

            self.assertIsNotNone(savedItem.data_ref)
            self.assertEqual(savedItem.data_ref.url_raw, hlp.to_db_format(self.dstRelPath))
            self.assertTrue(os.path.exists(os.path.join(self.repo.base_path,
                                                        savedItem.data_ref.url)))
            self.assertTrue(os.path.exists(self.srcAbsPath))
        finally:
            uow.close()

    def test_saveNewItemWithTags(self):
        userLogin = "user"
        item = db.Item(userLogin, "Item with tags")

        tagNameThatExistsInRepo = "Lyrics"
        tagNameNew = "No items in test repo with such Tag!"

        item.addTag(tagNameThatExistsInRepo, userLogin)
        item.addTag(tagNameNew, userLogin)

        try:
            uow = self.repo.createUnitOfWork()
            cmd = cmds.SaveNewItemCommand(item)
            savedItemId = uow.executeCommand(cmd)
        finally:
            uow.close()

        savedItem = self.getExistingItem(savedItemId)
        self.assertEqual(savedItem.title, item.title)
        self.assertTrue(savedItem.hasTag(tagNameThatExistsInRepo))
        self.assertTrue(savedItem.hasTag(tagNameNew))
        self.assertEqual(len(savedItem.item_tags), 2)


    def test_saveNewItemWithFields(self):
        userLogin = "user"
        item = db.Item(userLogin, "Item with fields")

        fieldOne = ("Year", 2012)
        fieldTwo = ("No items in test repo with such Field!", "Some value")

        item.setFieldValue(fieldOne[0], fieldOne[1], userLogin)
        item.setFieldValue(fieldTwo[0], fieldTwo[1], userLogin)

        try:
            uow = self.repo.createUnitOfWork()
            cmd = cmds.SaveNewItemCommand(item)
            savedItemId = uow.executeCommand(cmd)
        finally:
            uow.close()

        savedItem = self.getExistingItem(savedItemId)
        self.assertEqual(savedItem.title, item.title)
        self.assertTrue(savedItem.hasField(fieldOne[0], fieldOne[1]))
        self.assertTrue(savedItem.hasField(fieldTwo[0], fieldTwo[1]))
        self.assertEqual(len(savedItem.item_fields), 2)


class DeleteItemTest(AbstractTestCaseWithRepo):
    def test_deleteExistingItemWithExistingPhysicalFileByOwner(self):
        userThatDeletesItem = context.itemWithFile.ownerUserLogin
        try:
            uow = self.repo.createUnitOfWork()
            _itemBeforeDelete = uow.executeCommand(cmds.GetExpungedItemCommand(context.itemWithFile.id))

            cmd = cmds.DeleteItemCommand(context.itemWithFile.id, userThatDeletesItem,
                                    delete_physical_file=True)
            uow.executeCommand(cmd)
        finally:
            uow.close()

        try:
            uow = self.repo.createUnitOfWork()
            deletedItem = uow.executeCommand(cmds.GetExpungedItemCommand(context.itemWithFile.id))
            self.assertFalse(deletedItem.alive)
            self.assertIsNone(deletedItem.data_ref)

            #NOTE that tags/fields collections are not cleared, as you might expect
            self.assertTrue(len(deletedItem.item_tags) >= 0)
            self.assertTrue(len(deletedItem.item_fields) >= 0)

        finally:
            uow.close()
        self.assertFalse(os.path.exists(os.path.join(context.COPY_OF_TEST_REPO_BASE_PATH, context.itemWithFile.relFilePath)))






class UpdateItemTest(AbstractTestCaseWithRepo):

    def test_updateItemTitleByOwner(self):
        item = self.getExistingItem(context.itemWithFile.id)
        self.assertEqual(item.title, context.itemWithFile.title)

        #Change item's title
        newItemTitle = "ABCDEF"
        self.assertNotEqual(item.title, newItemTitle,
                            "You should change item's title to some different value.")
        item.title = newItemTitle

        newSrcAbsPath = os.path.join(self.repo.base_path, item.data_ref.url)
        newDstRelPath = item.data_ref.url
        self.updateExistingItem(item, newSrcAbsPath, newDstRelPath, item.user_login)

        #Get an item from repo again and check it's title
        item = self.getExistingItem(context.itemWithFile.id)
        self.assertEqual(item.title, newItemTitle)



    def test_updateItemTagsByOwner(self):
        userLogin = "user"
        item = self.getExistingItem(context.itemWithTagsAndFields.id)
        self.assertEqual(item.title, context.itemWithTagsAndFields.title)
        self.assertEqual(len(item.item_tags), len(context.itemWithTagsAndFields.tags))
        self.assertEqual(len(context.itemWithTagsAndFields.tags), 2)

        #Remove one existing tag
        tagNameToRemove = "RHCP"
        self.assertTrue(item.hasTag(tagNameToRemove))
        self.assertTrue(item.removeTag(tagNameToRemove))

        #Add one new tag
        tagNameToAdd = "TagNameToAdd"
        self.assertNotEqual(tagNameToRemove, tagNameToAdd)
        self.assertFalse(item.hasTag(tagNameToAdd))
        item.addTag(tagNameToAdd, userLogin)

        newSrcAbsPath = os.path.join(self.repo.base_path, item.data_ref.url)
        newDstRelPath = item.data_ref.url
        self.updateExistingItem(item, newSrcAbsPath, newDstRelPath, item.user_login)

        item = self.getExistingItem(context.itemWithTagsAndFields.id)
        self.assertFalse(item.hasTag(tagNameToRemove))
        self.assertTrue(item.hasTag(tagNameToAdd))
        self.assertTrue(item.hasTag("Lyrics"))
        self.assertEqual(len(item.item_tags), 2)


    def test_updateItemFieldsByOwner(self):
        userLogin = context.itemWithTagsAndFields.ownerUserLogin

        item = self.getExistingItem(context.itemWithTagsAndFields.id)
        self.assertEqual(item.title, context.itemWithTagsAndFields.title)
        self.assertEqual(len(item.item_fields), len(context.itemWithTagsAndFields.fields))
        self.assertEqual(len(context.itemWithTagsAndFields.fields), 4)

        #Remove one existing field
        fieldNameToRemove = "Year"
        self.assertTrue(item.hasField(fieldNameToRemove, 1991))
        self.assertTrue(item.removeField(fieldNameToRemove))

        #Add one new field
        fieldToAdd = ("FieldNameToAdd", "Some value")
        self.assertFalse(item.hasField(fieldToAdd[0]))
        item.setFieldValue(fieldToAdd[0], fieldToAdd[1], userLogin)

        #Edit one existing field
        fieldToEdit = ("Notes", "Some new notes")
        self.assertTrue(item.hasField(fieldToEdit[0]))
        self.assertFalse(item.hasField(fieldToEdit[0], fieldToEdit[1]))
        item.setFieldValue(fieldToEdit[0], fieldToEdit[1], userLogin)

        newSrcAbsPath = os.path.join(self.repo.base_path, item.data_ref.url)
        newDstRelPath = item.data_ref.url
        self.updateExistingItem(item, newSrcAbsPath, newDstRelPath, item.user_login)

        item = self.getExistingItem(context.itemWithTagsAndFields.id)
        self.assertFalse(item.hasField(fieldNameToRemove))
        self.assertTrue(item.hasField(fieldToAdd[0], fieldToAdd[1]))
        self.assertTrue(item.hasField(fieldToEdit[0], fieldToEdit[1]))
        self.assertTrue(item.hasField("Rating", 5))
        self.assertTrue(item.hasField("Albom", "Blood Sugar Sex Magik"))
        self.assertEqual(len(item.item_fields), 4)


    def test_addFileToItemWithoutFile(self):
        # Referenced file for new DataRef will be from the outside of the repo
        item = self.getExistingItem(context.itemWithoutFile.id)
        self.assertEqual(item.title, context.itemWithoutFile.title)
        self.assertIsNone(item.data_ref)
        self.assertFalse(os.path.exists(os.path.join(self.repo.base_path, "file.txt")))

        # Link file with the item, file should be in the repo root
        srcAbsPath = os.path.abspath(os.path.join(self.repo.base_path, "..", "tmp", "file.txt"))
        dstRelPath = "file.txt"
        self.updateExistingItem(item, srcAbsPath, dstRelPath, item.user_login)

        item = self.getExistingItem(context.itemWithoutFile.id)
        self.assertEqual(item.title, context.itemWithoutFile.title)
        self.assertIsNotNone(item.data_ref)
        self.assertEqual(item.data_ref.url, dstRelPath)
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, "file.txt")))


    def test_addFileToItemWithoutFileWithDestinationInsideRepo(self):
        # Referenced file for new DataRef will be from the outside of the repo
        # We will specify the destination path in the repo - where to put the file

        item = self.getExistingItem(context.itemWithoutFile.id)
        self.assertEqual(item.title, context.itemWithoutFile.title)
        self.assertIsNone(item.data_ref)
        self.assertFalse(os.path.exists(os.path.join(self.repo.base_path, "dir1", "dir2", "file.txt")))

        # Link file with the item
        newSrcAbsPath = os.path.abspath(os.path.join(self.repo.base_path, "..", "tmp", "file.txt"))
        newDstRelPath = os.path.join("dir1", "dir2", "copied_file.txt")
        self.updateExistingItem(item, newSrcAbsPath, newDstRelPath, item.user_login)

        item = self.getExistingItem(context.itemWithoutFile.id)
        self.assertEqual(item.title, context.itemWithoutFile.title)
        self.assertIsNotNone(item.data_ref)
        self.assertEqual(hlp.to_db_format(item.data_ref.url), "dir1/dir2/copied_file.txt")
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, "dir1", "dir2", "copied_file.txt")))
        self.assertFalse(os.path.isdir(os.path.join(self.repo.base_path, "dir1", "dir2", "copied_file.txt")))


    def test_moveFileOfItemToAnotherLocationWithinRepo(self):
        item = self.getExistingItem(context.itemWithTagsAndFields.id)
        self.assertEqual(item.title, context.itemWithTagsAndFields.title)
        self.assertIsNotNone(item.data_ref)
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, item.data_ref.url)))

        # Move linked file to another location within the repository
        newSrcAbsPath = os.path.join(self.repo.base_path, item.data_ref.url)
        path = ["new", "location", "for", "file", "I Could Have Lied.txt"]
        newDstRelPath = os.path.join(*path)
        self.updateExistingItem(item, newSrcAbsPath, newDstRelPath, item.user_login)

        item = self.getExistingItem(context.itemWithTagsAndFields.id)
        self.assertEqual(item.title, context.itemWithTagsAndFields.title)
        self.assertIsNotNone(item.data_ref)
        self.assertEqual(hlp.to_db_format(item.data_ref.url), "new/location/for/file/I Could Have Lied.txt")
        self.assertFalse(os.path.isdir(os.path.join(self.repo.base_path, *path)))
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, *path)))

    def test_moveFileOfItemToAnotherLocationWithinRepoAndRename(self):
        item = self.getExistingItem(context.itemWithTagsAndFields.id)
        self.assertEqual(item.title, context.itemWithTagsAndFields.title)
        self.assertIsNotNone(item.data_ref)
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, item.data_ref.url)))

        # Move linked file to another location within the repository
        # NOTE: File will be not only moved, but also renamed
        newSrcAbsPath = os.path.join(self.repo.base_path, item.data_ref.url)
        path = ["new", "location", "for", "file", "could_have_lied_lyrics.txt"]
        newDstRelPath = os.path.join(*path)
        self.updateExistingItem(item, newSrcAbsPath, newDstRelPath, item.user_login)

        item = self.getExistingItem(context.itemWithTagsAndFields.id)
        self.assertEqual(item.title, context.itemWithTagsAndFields.title)
        self.assertIsNotNone(item.data_ref)
        self.assertEqual(hlp.to_db_format(item.data_ref.url), "new/location/for/file/could_have_lied_lyrics.txt")
        self.assertFalse(os.path.isdir(os.path.join(self.repo.base_path, *path)))
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, *path)))

    def test_removeFileFromItem(self):
        item = self.getExistingItem(context.itemWithTagsAndFields.id)
        self.assertEqual(item.title, context.itemWithTagsAndFields.title)
        self.assertIsNotNone(item.data_ref)
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, item.data_ref.url)))

        self.updateExistingItem(item, None, None, item.user_login)

        item = self.getExistingItem(context.itemWithTagsAndFields.id)
        self.assertEqual(item.title, context.itemWithTagsAndFields.title)
        self.assertIsNone(item.data_ref)

        # Physical file should not be deleted
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, context.itemWithTagsAndFields.relFilePath)))

        #DataRef is deleted, because there is no other Items reference to it
        dataRef = self.getDataRef(context.itemWithTagsAndFields.relFilePath)
        self.assertIsNone(dataRef)

    def test_removeSharedFileFromItem(self):
        item = self.getExistingItem(context.itemNo1WithSharedFile.id)
        self.assertEqual(item.title, context.itemNo1WithSharedFile.title)
        self.assertIsNotNone(item.data_ref)
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, item.data_ref.url)))

        item2 = self.getExistingItem(context.itemNo2WithSharedFile.id)
        self.assertEqual(item2.title, context.itemNo2WithSharedFile.title)
        self.assertIsNotNone(item2.data_ref)
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, item2.data_ref.url)))

        self.assertEqual(item.data_ref.url, item2.data_ref.url, "File is shared by two items")

        self.updateExistingItem(item, None, None, item.user_login)

        item = self.getExistingItem(context.itemNo1WithSharedFile.id)
        self.assertEqual(item.title, context.itemNo1WithSharedFile.title)
        self.assertIsNone(item.data_ref)

        # Physical file should not be deleted
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path,
                                                    context.itemNo1WithSharedFile.relFilePath)))

        #DataRef is not deleted, because there is another Item, that reference to it
        dataRef = self.getDataRef(context.itemNo1WithSharedFile.relFilePath)
        self.assertIsNotNone(dataRef)


    def test_replaceFileOfItemWithAnotherOuterFile(self):
        # File of new DataRef will be from the outside of the repo
        item = self.getExistingItem(context.itemWithTagsAndFields.id)
        self.assertIsNotNone(item)

        # Link file with the item
        dstRelPath = "file.txt"
        srcAbsPath = os.path.abspath(os.path.join(self.repo.base_path, "..", "tmp", "file.txt"))
        self.updateExistingItem(item, srcAbsPath, dstRelPath, item.user_login)

        item = self.getExistingItem(context.itemWithTagsAndFields.id)
        self.assertEqual(item.title, context.itemWithTagsAndFields.title)
        self.assertIsNotNone(item.data_ref)
        self.assertEqual(item.data_ref.url, dstRelPath)
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, "file.txt")))

        # Old physical file should not be deleted
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, context.itemWithTagsAndFields.relFilePath)))

        #Old DataRef should be deleted after this operation
        dataRef = self.getDataRef(context.itemWithTagsAndFields.relFilePath)
        self.assertIsNone(dataRef)

    def test_replaceFileOfItemWithAnotherInnerFile(self):
        # File of new DataRef will be from the same repo.
        # But the new file is not a stored file (it has no corresponding DataRef object)
        item = self.getExistingItem(context.itemWithTagsAndFields.id)
        self.assertIsNotNone(item)
        self.assertIsNotNone(item.data_ref)
        self.assertEqual(hlp.to_db_format(item.data_ref.url), context.itemWithTagsAndFields.relFilePath)
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, item.data_ref.url)))

        # Link file with the item
        relUrl = os.path.join("this", "is", "untracked", "file.txt")
        absUrl = os.path.abspath(os.path.join(self.repo.base_path, relUrl))
        self.assertTrue(os.path.exists(absUrl))
        self.updateExistingItem(item, absUrl, relUrl, item.user_login)

        item = self.getExistingItem(context.itemWithTagsAndFields.id)
        self.assertEqual(item.title, context.itemWithTagsAndFields.title)
        self.assertIsNotNone(item.data_ref)
        self.assertEqual(item.data_ref.url, relUrl)
        self.assertTrue(os.path.exists(absUrl))

        # Old physical file should not be deleted
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, context.itemWithTagsAndFields.relFilePath)))

        #Old DataRef should be deleted after this operation
        dataRef = self.getDataRef(context.itemWithTagsAndFields.relFilePath)
        self.assertIsNone(dataRef)

    def test_replaceFileOfItemWithAnotherInnerStoredFile(self):
        # File of new DataRef will be from the same repo, and it will be
        # a stored file (linked with some other item)
        item = self.getExistingItem(context.itemWithTagsAndFields.id)
        self.assertIsNotNone(item)
        self.assertIsNotNone(item.data_ref)
        self.assertEqual(hlp.to_db_format(item.data_ref.url), context.itemWithTagsAndFields.relFilePath)
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, item.data_ref.url)))

        # Link file with the item
        relUrl = context.itemWithFile.relFilePath
        absUrl = os.path.abspath(os.path.join(self.repo.base_path, relUrl))
        self.assertTrue(os.path.exists(absUrl))

        self.updateExistingItem(item, absUrl, relUrl, item.user_login)

        item = self.getExistingItem(context.itemWithTagsAndFields.id)
        self.assertEqual(item.title, context.itemWithTagsAndFields.title)
        self.assertIsNotNone(item.data_ref)
        self.assertEqual(item.data_ref.url, relUrl)
        self.assertTrue(os.path.exists(absUrl))

        #Two different items now share same DataRef
        otherItem = self.getExistingItem(context.itemWithFile.id)
        self.assertIsNotNone(otherItem.data_ref)
        self.assertEquals(item.data_ref.id, otherItem.data_ref.id)

        # Old physical file should not be deleted
        self.assertTrue(os.path.exists(os.path.join(self.repo.base_path, context.itemWithTagsAndFields.relFilePath)))

        #Old DataRef should not be deleted after this operation
        dataRef = self.getDataRef(context.itemWithTagsAndFields.relFilePath)
        self.assertIsNone(dataRef)



    #def test_addTagsToItemByNotOwnerUser(self):
        #TODO implement test
    #    pass

    #def test_removeTagsFromItemByNotOwnerUser(self):
        #TODO implement test
    #    pass



class OtherCommandsTest(AbstractTestCaseWithRepo):

    def test_moveFileCommand(self):
        item = self.getExistingItem(context.itemWithTagsAndFields.id)
        self.assertIsNotNone(item.data_ref, "This item must have a file")
        
        fileAbsPath = os.path.join(self.repo.base_path, item.data_ref.url)
        self.assertTrue(os.path.exists(fileAbsPath))
        
        newFileRelPath = os.path.join("some", "new", "dir", os.path.basename(fileAbsPath))
        newFileAbsPath = os.path.join(self.repo.base_path, newFileRelPath)
        self.assertFalse(os.path.exists(newFileAbsPath))
        
        try:
            uow = self.repo.createUnitOfWork()
            cmd = cmds.MoveFileCommand(fileAbsPath, newFileAbsPath)
            uow.executeCommand(cmd)
        finally:
            uow.close()

        self.assertFalse(os.path.exists(fileAbsPath))
        self.assertTrue(os.path.exists(newFileAbsPath))

        try:
            uow = self.repo.createUnitOfWork()
            itemAfter = self.getExistingItem(context.itemWithTagsAndFields.id)
            self.assertEqual(itemAfter.data_ref.url, newFileRelPath)

        finally:
            uow.close()
            

    def test_renameFileCommand(self):
        item = self.getExistingItem(context.itemWithTagsAndFields.id)
        self.assertIsNotNone(item.data_ref, "This item must have a file")
        fileAbsPath = os.path.join(self.repo.base_path, item.data_ref.url)
        newFileName = "copy_of_" + os.path.basename(item.data_ref.url)
        newFileAbsPath = os.path.join(os.path.dirname(fileAbsPath), newFileName)
        try:
            uow = self.repo.createUnitOfWork()
            
            cmd = cmds.RenameFileCommand(fileAbsPath, newFileName)
            uow.executeCommand(cmd)
        finally:
            uow.close()

        try:
            uow = self.repo.createUnitOfWork()
            itemAfter = self.getExistingItem(context.itemWithTagsAndFields.id)
            self.assertEqual(os.path.relpath(newFileAbsPath, self.repo.base_path), itemAfter.data_ref.url)

        finally:
            uow.close()


    def test_renameDirectoryCommand(self):
        dirRelPath = os.path.join("lyrics", "RHCP")
        dirAbsPath = os.path.join(self.repo.base_path, dirRelPath)
        newDirName = "RedHotChiliPeppers"
        
        dataRefsBefore = self.getDataRefsFromDir(dirRelPath)
        self.assertTrue(len(dataRefsBefore) > 0, "There must be files in directory")
        for dataRef in dataRefsBefore:
            self.assertTrue(dataRef.url.startswith(dirRelPath))
        
        try:
            uow = self.repo.createUnitOfWork()
            cmd = cmds.RenameDirectoryCommand(dirAbsPath, newDirName)
            uow.executeCommand(cmd)
        finally:
            uow.close()

        dataRefsAfter = self.getDataRefsFromDir(dirRelPath)
        self.assertTrue(len(dataRefsAfter) == 0, "There must be no files in old directory")
        
        newDirRelPath = os.path.join(os.path.dirname(dirRelPath), newDirName)
        dataRefsAfter2 = self.getDataRefsFromDir(newDirRelPath)
        self.assertTrue(len(dataRefsAfter2) > 0, "There must be files in new directory")
        for dataRef in dataRefsAfter2:
            self.assertTrue(dataRef.url.startswith(newDirRelPath))
        

        
