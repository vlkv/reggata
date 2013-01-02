'''
Created on 20.12.2010 by  Vitaly Volkov
'''
import os
import datetime
from data.db_schema import Item, DataRef
from helpers import computeFileHash


class IntegrityFixerFactory(object):
    
    @staticmethod
    def createFixer(code, strategy, uow, repo_base_path, items_lock):
        if code == Item.ERROR_FILE_NOT_FOUND:
            return FileNotFoundFixer(strategy, uow, repo_base_path, items_lock)
        
        elif code == Item.ERROR_FILE_HASH_MISMATCH:
            return FileHashMismatchFixer(strategy, uow, repo_base_path, items_lock)
        
        else:
            assert False, "There is no fixer class for item integrity error code {0}.".format(code)


class AbstractIntegrityFixer(object):
    def __init__(self, uow, repoBasePath, itemsLock):
        super(AbstractIntegrityFixer, self).__init__()
        self.uow = uow
        self.repo_base_path = repoBasePath
        self.lock = itemsLock
        
    def code(self):
        raise NotImplementedError("Should be implemented in a subclass")
    
    def fix_error(self, item, user_login):
        raise NotImplementedError("Should be implemented in a subclass")
    
    def _searchExistingMatchedDataRef(self, originalDataRef):
        '''
            Returns (isFound, matchedDataRef) tuple.
        '''
        found = False
        matchedDataRef = None
        try:
            matchedDataRef = self.uow.session.query(DataRef) \
                .filter(DataRef.hash == originalDataRef.hash) \
                .filter(DataRef.url_raw != originalDataRef.url_raw) \
                .first()
            if matchedDataRef is not None:
                # We must recalculate hash of found DataRef object, to be absolutely sure that it is correct
                recalculatedHash = computeFileHash(os.path.join(self.repo_base_path, matchedDataRef.url))
                if recalculatedHash == matchedDataRef.hash:
                    found = True
                else:
                    found = False
                    matchedDataRef = None
        except:
            found = False
            matchedDataRef = None
            
        return (found, matchedDataRef)
        
    def _searchUntrackedMatchedFile(self, originalDataRef):
        #TODO We should first search in the same directory (maybe this file was just renamed)
        newDataRef = None 
        needBreak = False
        for root, dirs, files in os.walk(self.repo_base_path):
            for file in files:
                #Skip files which size is different from originalDataRef.size
                size = os.path.getsize(os.path.join(root, file))
                if size != originalDataRef.size:
                    continue
                
                calculatedHash = computeFileHash(os.path.join(root, file))
                if calculatedHash != originalDataRef.hash:
                    continue
                
                fileRelPath = os.path.relpath(os.path.join(root, file), self.repo_base_path)
                newDataRef = DataRef(type=DataRef.FILE, url=fileRelPath, date_created=datetime.datetime.today())
                newDataRef.hash = calculatedHash
                newDataRef.size = os.path.getsize(os.path.join(root, file))
                self.uow.session.add(newDataRef)
                self.uow.session.flush()
                
                needBreak = True
                break
            
            if needBreak:
                break
            
        return newDataRef
        
    def _processItemsDataRef(self, item, matchedDataRef):
        self._tryToDeleteOriginalDataRef(item.data_ref)
        self._linkItemWithMatchedDataRef(item, matchedDataRef)
        return True
        
        
    def _tryToDeleteOriginalDataRef(self, originalDataRef):
        # TODO: we should not delete DataRef if there are existing other Items that reference to it!
        rows = self.uow.session.query(DataRef) \
            .filter(DataRef.id==originalDataRef.id) \
            .delete(synchronize_session=False)
        if rows == 0:
            raise Exception("Cannot delete data_ref object.")
        elif rows > 1:
            raise Exception("The query deleted {} data_ref objects (but it should delete only one).")


    def _linkItemWithMatchedDataRef(self, item, matchedDataRef):
        assert matchedDataRef is not None
        item_0 = self.uow.session.query(Item).filter(Item.id==item.id).one()
        item_0.data_ref_id = matchedDataRef.id
        item_0.data_ref = matchedDataRef
        self.uow.session.flush()
        self.uow.session.expunge(item_0)
    
    
        
    def _try_find(self, item, user_login):
        
        existingDataRefFound, dataRef = self._searchExistingMatchedDataRef(item.data_ref)
        if existingDataRefFound:
            assert dataRef is not None
            self._processItemsDataRef(item, dataRef)
        else:
            dataRef = self._searchUntrackedMatchedFile(item.data_ref)
            if dataRef is not None:
                self._processItemsDataRef(item, dataRef)
                
        if dataRef is not None:
            if dataRef in self.uow.session:
                self.uow.session.expunge(dataRef)
            
            try:
                self.lock.lockForWrite()
                item.data_ref = dataRef
            finally:
                self.lock.unlock()
        
        return dataRef is not None
        
    
class FileNotFoundFixer(AbstractIntegrityFixer):
    '''
        TRY_FIND - Fixer tries to find a file with matching hash. There are two cases here:
        a) Fixer finds an untracked file in the repo. A new DataRef object is created and it is 
    liked with the Item.
        b) Fixer finds a stored file so there is an existing DataRef object for the found file.
    Fixer links the Item with this found DataRef object.
        In both cases the original DataRef object will be deleted if there are no more references 
    to it from other Items.
        DELETE - Fixer just removes a reference from Item to the DataRef object. The original DataRef 
    object will be deleted if there are no more references to it from other Items. 
    '''
    TRY_FIND = 0
    DELETE = 1
    
    def __init__(self, strategy, uow, repo_base_path, items_lock):
        super(FileNotFoundFixer, self).__init__(uow, repo_base_path, items_lock)
        
        self.strategy = strategy
        self.uow = uow
        self.repo_base_path = repo_base_path
        self.lock = items_lock
    
    
    def code(self):
        return Item.ERROR_FILE_NOT_FOUND
    
    
    def fix_error(self, item, user_login):
        if item.data_ref is None:
            raise Exception("Given item has no referenced files. There is nothing to fix.")
        
        if self.strategy == self.TRY_FIND:
            return self._try_find(item, user_login)
        
        elif self.strategy == self.DELETE:
            return self._delete(item, user_login)
        
        else:
            raise ValueError("Not supported strategy = {0}.".format(self.strategy))


    def _delete(self, item, user_login):
        '''
            Deletes item.data_ref object, which links to the lost file.
        '''
        existingDataRef = self.uow.session.query(DataRef).get(item.data_ref.id)
        self.uow.session.delete(existingDataRef)
        self.uow.session.flush()
        
        try:
            self.lock.lockForWrite()
            item.data_ref_id = None
            item.data_ref = None            
        finally:
            self.lock.unlock()
        
        return True
        
    
        

class FileHashMismatchFixer(AbstractIntegrityFixer):
    '''
        TRY_FIND_FILE - Fixer tries to find a file with matching hash. There are two cases here:
        a) Fixer finds an untracked file in the repo. A new DataRef object is created and it is 
    liked with the Item.
        b) Fixer finds a stored file so there is an existing DataRef object for the found file.
    Fixer links the Item with this found DataRef object.
        In both cases the original DataRef object will be deleted if there are no more references 
    to it from other Items.
        UPDATE_HASH - Fixer calculates new hash for the file and stores it's value 
    in existing DataRef object of the Item. NOTE: We cannot create new DataRef object, 
    without deleting the original one (because url must be unique). 
    But we cannot delete original DataRef object if there are some items that reference to it.    
    '''
    TRY_FIND_FILE = 0
    UPDATE_HASH = 1
    
    def __init__(self, strategy, uow, repo_base_path, items_lock):
        super(FileHashMismatchFixer, self).__init__(uow, repo_base_path, items_lock)
        
        self.strategy = strategy
        self.uow = uow
        self.repo_base_path = repo_base_path
        self.lock = items_lock
        self.seen_files = dict()
        
    
    def code(self):
        return Item.ERROR_FILE_HASH_MISMATCH
    
    
    def fix_error(self, item, user_login):
        if item.data_ref is None:
            raise Exception("Given item has no referenced files. There is nothing to fix.")
        
        if self.strategy == self.UPDATE_HASH:
            return self._update_hash(item, user_login)
        
        elif self.strategy == self.TRY_FIND_FILE:
            return self._try_find(item, user_login)
        
        else:
            raise ValueError("Not supported strategy = {0}.".format(self.strategy))
    
    
    def _update_hash(self, item, user_login):
        filename = os.path.join(self.repo_base_path, item.data_ref.url)
        new_hash = computeFileHash(filename)
        new_size = os.path.getsize(filename)
        new_date_hashed = datetime.datetime.today()
        
        data_ref = self.uow.session.query(DataRef).get(item.data_ref.id)
        if data_ref.hash == new_hash and data_ref.size == new_size:
            raise Exception("This item.data_ref already has correct hash and size values.")
        
        data_ref.hash = new_hash
        data_ref.size = new_size
        data_ref.date_hashed = new_date_hashed 
        self.uow.session.flush()
        
        try:
            self.lock.lockForWrite()
            item.data_ref.hash = new_hash
            item.data_ref.size = new_size
            item.data_ref.date_hashed = new_date_hashed
        finally:
            self.lock.unlock()   
            
        return True
    
    


