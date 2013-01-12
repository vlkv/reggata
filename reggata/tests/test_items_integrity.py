'''
Created on 16.09.2012
@author: vlkv
'''
from PyQt4 import QtCore
from reggata.tests.abstract_test_cases import AbstractTestCaseWithRepo
from reggata.data import db_schema
from reggata.data.integrity_fixer import IntegrityFixerFactory, FileNotFoundFixer, FileHashMismatchFixer
from reggata.data.commands import CheckItemIntegrityCommand
import reggata.tests.tests_context as ctx
import os



class CheckItemIntegrityTest(AbstractTestCaseWithRepo):

    def test_checkItemWithoutErrors(self):
        item = self.getExistingItem(ctx.itemWithFile.id)
        uow = self.repo.createUnitOfWork()
        try:
            cmd = CheckItemIntegrityCommand(item, self.repo.base_path)
            errors = uow.executeCommand(cmd)
            self.assertTrue(len(errors) == 0)
        finally:
            uow.close()


    def test_checkItemWithErrorFileNotFound(self):
        item = self.getExistingItem(ctx.itemWithErrorFileNotFound.id)
        uow = self.repo.createUnitOfWork()
        try:
            cmd = CheckItemIntegrityCommand(item, self.repo.base_path)
            errors = uow.executeCommand(cmd)
            self.assertTrue(len(errors) == 1)
            self.assertTrue(db_schema.Item.ERROR_FILE_NOT_FOUND in errors)
        finally:
            uow.close()

    def test_checkItemWithErrorFileHashMismatch(self):
        item = self.getExistingItem(ctx.itemWithErrorHashMismatch.id)
        uow = self.repo.createUnitOfWork()
        try:
            cmd = CheckItemIntegrityCommand(item, self.repo.base_path)
            errors = uow.executeCommand(cmd)
            self.assertTrue(len(errors) == 1)
            self.assertTrue(db_schema.Item.ERROR_FILE_HASH_MISMATCH in errors)
        finally:
            uow.close()


class FixItemIntegrityTest(AbstractTestCaseWithRepo):

    def test_fixItemWithErrorFileNotFound_TryFind_UntrackedFile(self):
        '''
            Fixer should find an untracked file in the repo in a different location. And a new
        DataRef object will be created for it. Original DataRef object will be deleted
         (if no other items reference to it).
        '''
        item = self.getExistingItem(ctx.itemWithErrorFileNotFound.id)
        originalDataRefId = item.data_ref.id

        uow = self.repo.createUnitOfWork()
        try:
            itemsLock = QtCore.QReadWriteLock()
            fixer = IntegrityFixerFactory.createFixer(db_schema.Item.ERROR_FILE_NOT_FOUND,
                                              FileNotFoundFixer.TRY_FIND,
                                              uow, self.repo.base_path, itemsLock)
            result = fixer.fix_error(item, ctx.itemWithErrorFileNotFound.ownerUserLogin)
            uow.session.commit()
            self.assertTrue(result)
        finally:
            uow.close()

        fixedItem = self.getExistingItem(ctx.itemWithErrorFileNotFound.id)

        self.assertNotEquals(originalDataRefId, fixedItem.data_ref.id,
            "A new DataRef object should be created")

        originalDataRef = self.getDataRefById(originalDataRefId)
        self.assertIsNone(originalDataRef,
            "Original DataRef should be deleted, because there are no references to it anymore")

        foundFileAbsPath = os.path.join(self.repo.base_path, "this", "is", "lost", "consts.py")
        fixedItemFileAbsPath = os.path.join(self.repo.base_path, fixedItem.data_ref.url)

        self.assertEquals(fixedItemFileAbsPath, foundFileAbsPath,
            "Item should reference to this file now {}".format(foundFileAbsPath))

        self.assertTrue(os.path.exists(fixedItemFileAbsPath),
            "Found file should exist on filesystem")




    def test_fixItemWithErrorFileNotFound_TryFind_StoredFile(self):
        '''
            Fixer should find in the repo an existing DataRef object with the same matching hash.
        Original DataRef object should be deleted (if no other items reference to it).
        '''
        item = self.getExistingItem(ctx.itemWithErrorFileNotFoundNo2.id)
        originalDataRefId = item.data_ref.id

        uow = self.repo.createUnitOfWork()
        try:
            itemsLock = QtCore.QReadWriteLock()
            fixer = IntegrityFixerFactory.createFixer(db_schema.Item.ERROR_FILE_NOT_FOUND,
                                              FileNotFoundFixer.TRY_FIND,
                                              uow, self.repo.base_path, itemsLock)
            result = fixer.fix_error(item, ctx.itemWithErrorFileNotFoundNo2.ownerUserLogin)
            uow.session.commit()
            self.assertTrue(result)
        finally:
            uow.close()

        fixedItem = self.getExistingItem(ctx.itemWithErrorFileNotFoundNo2.id)
        self.assertEquals(fixedItem.data_ref.url_raw, ctx.itemId_1.relFilePath,
            "Fixed should find this stored file")

        fixedItemFileAbsPath = os.path.join(self.repo.base_path, fixedItem.data_ref.url)
        self.assertTrue(os.path.exists(fixedItemFileAbsPath),
            "Found file should exist on filesystem")

        originalDataRef = self.getDataRefById(originalDataRefId)
        self.assertIsNone(originalDataRef,
            "Original DataRef object should be deleted from database: no more references to it")

        anotherItem = self.getExistingItem(ctx.itemId_1.id)
        self.assertEquals(fixedItem.data_ref.id, anotherItem.data_ref.id,
            "Now two different items reference to the same DataRef object")




    def test_fixItemWithErrorFileNotFound_Delete(self):
        '''
            Fixer should just delete Item's reference to the lost file and delete original
        DataRef object from database (if no other items reference to it).
        '''
        item = self.getExistingItem(ctx.itemWithErrorFileNotFound.id)
        originalDataRefId = item.data_ref.id

        uow = self.repo.createUnitOfWork()
        try:
            itemsLock = QtCore.QReadWriteLock()
            fixer = IntegrityFixerFactory.createFixer(db_schema.Item.ERROR_FILE_NOT_FOUND,
                                              FileNotFoundFixer.DELETE,
                                              uow, self.repo.base_path, itemsLock)
            result = fixer.fix_error(item, ctx.itemWithErrorFileNotFound.ownerUserLogin)
            uow.session.commit()
            self.assertTrue(result)
        finally:
            uow.close()

        fixedItem = self.getExistingItem(ctx.itemWithErrorFileNotFound.id)
        self.assertIsNone(fixedItem.data_ref,
            "Item has no references to files now")

        originalDataRef = self.getDataRefById(originalDataRefId)
        self.assertIsNone(originalDataRef,
            "Original DataRef object should be deleted from database: no more references to it")


    def test_fixItemWithErrorHashMismatch_UpdateHash(self):
        '''
            Fixer should update file hash of an existing DataRef object.
        NOTE: We cannot create new DataRef object, without deleting the original one
        (because url must be unique). But we cannot delete original DataRef object
        if there are some items that reference to it.
        '''
        item = self.getExistingItem(ctx.itemWithErrorHashMismatch.id)
        originalDataRefId = item.data_ref.id
        originalFileHash = item.data_ref.hash
        originalFilePath = item.data_ref.url_raw

        uow = self.repo.createUnitOfWork()
        try:
            itemsLock = QtCore.QReadWriteLock()
            fixer = IntegrityFixerFactory.createFixer(db_schema.Item.ERROR_FILE_HASH_MISMATCH,
                                              FileHashMismatchFixer.UPDATE_HASH,
                                              uow, self.repo.base_path, itemsLock)
            result = fixer.fix_error(item, ctx.itemWithErrorHashMismatch.ownerUserLogin)
            uow.session.commit()
            self.assertTrue(result)
        finally:
            uow.close()

        fixedItem = self.getExistingItem(ctx.itemWithErrorHashMismatch.id)

        self.assertEqual(fixedItem.data_ref.id, originalDataRefId,
            "An Existing DataRef object should have been modified")

        self.assertNotEquals(fixedItem.data_ref.hash, originalFileHash,
            "File hash should be different")

        self.assertEquals(fixedItem.data_ref.url_raw, originalFilePath,
            "File path should not be changed")







    def test_fixItemWithErrorHashMismatch_TryFind_UntrackedFile(self):
        '''
            Fixer should find an untracked file with matching hash. A new DataRef object
        should be created for it. Original DataRef object will be deleted,
        because other items do not reference to it
        '''
        item = self.getExistingItem(ctx.itemWithErrorHashMismatch.id)
        originalDataRefId = item.data_ref.id
        originalFileHash = item.data_ref.hash

        uow = self.repo.createUnitOfWork()
        try:
            itemsLock = QtCore.QReadWriteLock()
            fixer = IntegrityFixerFactory.createFixer(db_schema.Item.ERROR_FILE_HASH_MISMATCH,
                                              FileHashMismatchFixer.TRY_FIND_FILE,
                                              uow, self.repo.base_path, itemsLock)
            result = fixer.fix_error(item, ctx.itemWithErrorHashMismatch.ownerUserLogin)
            uow.session.commit()
            self.assertTrue(result)
        finally:
            uow.close()

        fixedItem = self.getExistingItem(ctx.itemWithErrorHashMismatch.id)

        self.assertNotEquals(originalDataRefId, fixedItem.data_ref.id,
            "A new DataRef object should be created")

        originalDataRef = self.getDataRefById(originalDataRefId)
        self.assertIsNone(originalDataRef,
            "Original DataRef should be deleted, because there are no references to it anymore")

        foundFileAbsPath = os.path.join(self.repo.base_path, "this", "is", "untracked", "led_zeppelin_from_wikipedia.txt.original")
        fixedItemFileAbsPath = os.path.join(self.repo.base_path, fixedItem.data_ref.url)

        self.assertEquals(fixedItemFileAbsPath, foundFileAbsPath,
            "Item should reference to this file now {}".format(foundFileAbsPath))

        self.assertTrue(os.path.exists(fixedItemFileAbsPath),
            "Found file should exist on filesystem")

        self.assertEquals(fixedItem.data_ref.hash, originalFileHash,
            "File hash should be still the same")



    def test_fixItemWithErrorHashMismatch_TryFind_StoredFile(self):
        '''
            Fixer should find an existing DataRef object with matching file hash.
        Original DataRef object will be deleted, because other items do not reference to it.
        '''
        item = self.getExistingItem(ctx.itemWithErrorHashMismatchNo2.id)
        originalDataRefId = item.data_ref.id
        originalFileHash = item.data_ref.hash

        uow = self.repo.createUnitOfWork()
        try:
            itemsLock = QtCore.QReadWriteLock()
            fixer = IntegrityFixerFactory.createFixer(db_schema.Item.ERROR_FILE_HASH_MISMATCH,
                                              FileHashMismatchFixer.TRY_FIND_FILE,
                                              uow, self.repo.base_path, itemsLock)
            result = fixer.fix_error(item, ctx.itemWithErrorHashMismatchNo2.ownerUserLogin)
            uow.session.commit()
            self.assertTrue(result)
        finally:
            uow.close()

        fixedItem = self.getExistingItem(ctx.itemWithErrorHashMismatchNo2.id)

        fixedItemFileAbsPath = os.path.join(self.repo.base_path, fixedItem.data_ref.url)
        self.assertTrue(os.path.exists(fixedItemFileAbsPath),
            "Found file should exist on filesystem")

        originalDataRef = self.getDataRefById(originalDataRefId)
        self.assertIsNone(originalDataRef,
            "Original DataRef object should be deleted")

        self.assertEquals(fixedItem.data_ref.url_raw, ctx.itemId_4.relFilePath,
            "Fixer should have been found this file")

        self.assertEquals(originalFileHash, fixedItem.data_ref.hash,
            "File hash should be still the same")

        anotherItem = self.getExistingItem(ctx.itemId_4.id)
        self.assertEquals(fixedItem.data_ref.id, anotherItem.data_ref.id,
            "Now two items reference to the same DataRef object")
