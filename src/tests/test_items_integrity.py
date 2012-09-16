'''
Created on 16.09.2012
@author: vlkv
'''
from PyQt4 import QtCore
from tests.abstract_test_cases import AbstractTestCaseWithRepo
from tests.tests_context import *
from data import db_schema
from data.integrity_fixer import IntegrityFixerFactory, FileNotFoundFixer, FileHashMismatchFixer
from data.commands import CheckItemIntegrityCommand

   
    
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
    
    def test_fixItemWithErrorFileNotFound_TryFind_UntrackedFile(self):
        '''
            Fixer should find an untracked file in the repo in a different location. And a new 
        DataRef object will be created for it. Original DataRef object will be deleted 
         (if no other items reference to it).
        '''
        item = self.getExistingItem(itemWithErrorFileNotFound.id)
        originalDataRefId = item.data_ref.id
        
        uow = self.repo.createUnitOfWork()
        try:
            itemsLock = QtCore.QReadWriteLock()
            fixer = IntegrityFixerFactory.createFixer(db_schema.Item.ERROR_FILE_NOT_FOUND, 
                                              FileNotFoundFixer.TRY_FIND, 
                                              uow, self.repo.base_path, itemsLock)
            result = fixer.fix_error(item, itemWithErrorFileNotFound.ownerUserLogin)
            uow.session.commit()
            self.assertTrue(result)
        finally:
            uow.close()
            
        fixedItem = self.getExistingItem(itemWithErrorFileNotFound.id)
        
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
        item = self.getExistingItem(itemWithErrorFileNotFoundNo2.id)
        originalDataRefId = item.data_ref.id
        
        uow = self.repo.createUnitOfWork()
        try:
            itemsLock = QtCore.QReadWriteLock()
            fixer = IntegrityFixerFactory.createFixer(db_schema.Item.ERROR_FILE_NOT_FOUND, 
                                              FileNotFoundFixer.TRY_FIND, 
                                              uow, self.repo.base_path, itemsLock)
            result = fixer.fix_error(item, itemWithErrorFileNotFoundNo2.ownerUserLogin)
            uow.session.commit()    
            self.assertTrue(result)
        finally:
            uow.close()
            
        fixedItem = self.getExistingItem(itemWithErrorFileNotFoundNo2.id)
        self.assertEquals(fixedItem.data_ref.url_raw, itemId_1.relFilePath,
            "Fixed should find this stored file")
        
        fixedItemFileAbsPath = os.path.join(self.repo.base_path, fixedItem.data_ref.url)
        self.assertTrue(os.path.exists(fixedItemFileAbsPath),
            "Found file should exist on filesystem")
        
        originalDataRef = self.getDataRefById(originalDataRefId)
        self.assertIsNone(originalDataRef, 
            "Original DataRef object should be deleted from database: no more references to it")
        
        anotherItem = self.getExistingItem(itemId_1.id)
        self.assertEquals(fixedItem.data_ref.id, anotherItem.data_ref.id, 
            "Now two different items reference to the same DataRef object")
        
        
        
        
    def test_fixItemWithErrorFileNotFound_Delete(self):
        '''
            Fixer should just delete Item's reference to the lost file and delete original 
        DataRef object from database (if no other items reference to it).
        '''
        item = self.getExistingItem(itemWithErrorFileNotFound.id)
        originalDataRefId = item.data_ref.id
        
        uow = self.repo.createUnitOfWork()
        try:
            itemsLock = QtCore.QReadWriteLock()
            fixer = IntegrityFixerFactory.createFixer(db_schema.Item.ERROR_FILE_NOT_FOUND, 
                                              FileNotFoundFixer.DELETE, 
                                              uow, self.repo.base_path, itemsLock)
            result = fixer.fix_error(item, itemWithErrorFileNotFound.ownerUserLogin)
            uow.session.commit()
            self.assertTrue(result)
        finally:
            uow.close()
            
        fixedItem = self.getExistingItem(itemWithErrorFileNotFound.id)
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
        item = self.getExistingItem(itemWithErrorHashMismatch.id)
        originalDataRefId = item.data_ref.id
        originalFileHash = item.data_ref.hash
        originalFilePath = item.data_ref.url_raw
        uow = self.repo.createUnitOfWork()
        try:
            itemsLock = QtCore.QReadWriteLock()
            fixer = IntegrityFixerFactory.createFixer(db_schema.Item.ERROR_FILE_HASH_MISMATCH, 
                                              FileHashMismatchFixer.UPDATE_HASH, 
                                              uow, self.repo.base_path, itemsLock)
            result = fixer.fix_error(item, itemWithErrorHashMismatch.ownerUserLogin)
            uow.session.commit()
            
            self.assertTrue(result)
            
        finally:
            uow.close()
        
        fixedItem = self.getExistingItem(itemWithErrorHashMismatch.id)
        self.assertNotEqual(fixedItem.data_ref.id, originalDataRefId, 
            "A new DataRef object should have been created")
        
        originalDataRef = self.getDataRefById(originalDataRefId)
        self.assertIsNone(originalDataRef,
            "Original DataRef object should be deleted")
        
        
        

            
            
    def test_fixItemWithErrorHashMismatch_TryFind_UntrackedFile(self):
        '''
            Fixer should find an untracked file with matching hash. A new DataRef object 
        should be created for it. Original DataRef object will be deleted, 
        because other items do not reference to it
        '''
        item = self.getExistingItem(itemWithErrorHashMismatch.id)
        originalDataRefId = item.data_ref.id
        originalDataRefUrl = item.data_ref.url_raw
        originalFileHash = item.data_ref.hash
        uow = self.repo.createUnitOfWork()
        try:
            itemsLock = QtCore.QReadWriteLock()
            fixer = IntegrityFixerFactory.createFixer(db_schema.Item.ERROR_FILE_HASH_MISMATCH, 
                                              FileHashMismatchFixer.TRY_FIND_FILE, 
                                              uow, self.repo.base_path, itemsLock)
            result = fixer.fix_error(item, itemWithErrorHashMismatch.ownerUserLogin)
            uow.session.commit()
            
            self.assertTrue(result)
            
        finally:
            uow.close()
        
        fixedItem = self.getExistingItem(itemWithErrorHashMismatch.id)
        #TODO: write correct checks
        
    def test_fixItemWithErrorHashMismatch_TryFind_StoredFile(self):
        '''
            Fixer should find an existing DataRef object with matching file hash.
        Original DataRef object will be deleted, because other items do not reference to it.
        '''
        item = self.getExistingItem(itemWithErrorHashMismatchNo2.id)
        originalDataRefId = item.data_ref.id
        originalDataRefUrl = item.data_ref.url_raw
        originalFileHash = item.data_ref.hash
        uow = self.repo.createUnitOfWork()
        try:
            itemsLock = QtCore.QReadWriteLock()
            fixer = IntegrityFixerFactory.createFixer(db_schema.Item.ERROR_FILE_HASH_MISMATCH, 
                                              FileHashMismatchFixer.TRY_FIND_FILE, 
                                              uow, self.repo.base_path, itemsLock)
            result = fixer.fix_error(item, itemWithErrorHashMismatchNo2.ownerUserLogin)
            uow.session.commit()
            
            self.assertTrue(result)
            
        finally:
            uow.close()
        
        fixedItem = self.getExistingItem(itemWithErrorHashMismatchNo2.id)
        
        fixedItemFileAbsPath = os.path.join(self.repo.base_path, fixedItem.data_ref.url)
        self.assertTrue(os.path.exists(fixedItemFileAbsPath),
            "Found file should exist on filesystem")
        
        originalDataRef = self.getDataRefById(originalDataRefId)
        self.assertIsNone(originalDataRef, 
            "Original DataRef object should be deleted")
        
        self.assertEquals(fixedItem.data_ref.url_raw, itemId_4.relFilePath, 
            "Fixer should have been found this file")
        
        self.assertEquals(originalFileHash, fixedItem.data_ref.hash,
            "File hash should be still the same")
        
        anotherItem = self.getExistingItem(itemId_4.id)
        self.assertEquals(fixedItem.data_ref.id, anotherItem.data_ref.id,
            "Now two items reference to the same DataRef object")
        
        
        
            