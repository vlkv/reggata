# -*- coding: utf-8 -*-
'''
Created on 20.12.2010 by  Vitaly Volkov
'''
from data.db_schema import Item, DataRef
from data import repo_mgr
from helpers import compute_hash
import os
import datetime

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
    def code(self):
        raise NotImplementedError("Should be implemented in a subclass")
    
    def fix_error(self, item, user_login):
        raise NotImplementedError("Should be implemented in a subclass")
        
    
class FileNotFoundFixer(AbstractIntegrityFixer):
    TRY_FIND = 0
    DELETE = 1
    
    def __init__(self, strategy, uow, repo_base_path, items_lock):
        if strategy not in [self.TRY_FIND, self.TRY_FIND_ELSE_DELETE, self.DELETE]:
            raise Exception("Wrong strategy value {0}".format(strategy))
        
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
            raise Exception("Not supported strategy = {0}.".format(self.strategy))


    def _delete(self, item, user_login):
        '''
            This method deletes item.data_ref object, which links to the lost file.
        '''
        #updating existing DataRef object
        existing_dr = self.uow.session.query(DataRef).get(item.data_ref.id)
        self.uow.session.delete(existing_dr)
        self.uow.session.flush()
        
        if existing_dr in self.uow.session:
            self.uow.session.expunge(existing_dr)            
        
        try:
            self.lock.lockForWrite()
            item.data_ref_id = None
            item.data_ref = None            
        finally:
            self.lock.unlock()
        
        return True
        
        
    def _try_find(self, item, user_login):
        error_fixed = False
        delete_old_dr = False
        bind_new_dr_to_item = False
        new_dr = None        
        
        found = None
        
        try:
            #Сначала нужно поискать среди существующих DataRef-ов в базе
            new_dr = self.uow.session.query(DataRef).filter(DataRef.hash==item.data_ref.hash)\
                .filter(DataRef.url_raw != item.data_ref.url).first()
            if new_dr is not None:
                hash = compute_hash(os.path.join(self.repo_base_path, new_dr.url))
                if hash == item.data_ref.hash and hash == new_dr.hash:
                    delete_old_dr = True
                    bind_new_dr_to_item = True
                    found = True
                    error_fixed = True
                else:
                    new_dr = None
        except:
            found = False
        
        if not found:
            #TODO We should first search in the same directory (maybe this file was just renamed) 
            need_break = False
            for root, dirs, files in os.walk(self.repo_base_path):
                for file in files:
                    
                    #Skip files which size is different from item.data_ref.size
                    size = os.path.getsize(os.path.join(root, file))
                    if size != item.data_ref.size:
                        continue
                    
                    hash = compute_hash(os.path.join(root, file))
                    if hash == item.data_ref.hash:
                        #updating existing DataRef object
                        new_dr = self.uow.session.query(DataRef).get(item.data_ref.id)
                        new_dr.url = os.path.relpath(os.path.join(root, file), self.repo_base_path)
                        self.uow.session.flush()
                        error_fixed = True
                        
                        need_break = True
                        break
                if need_break:        
                    break
                
        if delete_old_dr:
            rows = self.uow.session.query(DataRef).filter(DataRef.id==item.data_ref.id)\
                .delete(synchronize_session=False)
            if rows == 0:
                raise Exception("Cannot delete data_ref object.")
            elif rows > 1:
                raise Exception("The query deleted {} data_ref objects (but it should delete only one).")
        
        if bind_new_dr_to_item and new_dr is not None:
            item_0 = self.uow.session.query(Item).filter(Item.id==item.id).one()
            item_0.data_ref_id = new_dr.id
            item_0.data_ref = new_dr
            self.uow.session.flush()
            self.uow.session.expunge(item_0)
                
        if new_dr is not None:
            if new_dr in self.uow.session:
                self.uow.session.expunge(new_dr)            
            
            try:
                self.lock.lockForWrite()
                item.data_ref = new_dr
            finally:
                self.lock.unlock()
        
        return error_fixed 
        
        

class FileHashMismatchFixer(AbstractIntegrityFixer):
    TRY_FIND_FILE = 0
    UPDATE_HASH = 1
    
    def __init__(self, strategy, uow, repo_base_path, items_lock):
        if strategy not in [self.UPDATE_HASH, self.TRY_FIND_FILE]:
            raise Exception("Wrong strategy value {0}".format(strategy))
        
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
            return self._try_find_file(item, user_login)
        
        else:
            raise Exception("Not supported strategy = {0}.".format(self.strategy))
    
    
    def _update_hash(self, item, user_login):
        #Вычисляем новый хеш и размер файла
        filename = os.path.join(self.repo_base_path, item.data_ref.url)
        new_hash = compute_hash(filename)
        new_size = os.path.getsize(filename)
        new_date_hashed = datetime.datetime.today()
        
        #Извлекаем копию data_ref из БД, данный объект будет принадлежать текущей сессии
        data_ref = self.uow.session.query(DataRef).get(item.data_ref.id)
        if data_ref.hash == new_hash and data_ref.size == new_size:
            raise Exception("This item.data_ref already has correct hash and size values.")
        
        #Меняем только эти три поля!
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
    
    
    def _try_find_file(self, item, user_login):
        #Пытаемся найти внутри хранилища файл, хеш которого совпадает с item.data_ref.hash
        #Если нашли, то привязываем item к найденному файлу. 
        #При этом либо придется отредактировать url у существующего data_ref объекта, либо 
        #привязаться к другому data_ref объекту.

        error_fixed = False
        delete_old_dr = False
        bind_new_dr_to_item = False
        new_dr = None
        
        found = None
        
        try:
            #Сначала имеет смысл поискать среди имеющихся DataRef объектов. Потому что один и тот же
            #файл может присутствовать в хранилище дважды (но по разным путям)
            other_dr = self.uow.session.query(DataRef).filter(DataRef.hash==item.data_ref.hash)\
                .filter(DataRef.url_raw != item.data_ref.url).first()
            if other_dr is not None:
                #Вычисляем хеш для найденного файла и сравниваем, а то вдруг этот файл тоже с ошибкой?
                hash = compute_hash(os.path.join(self.repo_base_path, other_dr.url))
                self.seen_files[os.path.join(self.repo_base_path, other_dr.url)] = hash
                if hash == item.data_ref.hash and hash == other_dr.hash:
                    delete_old_dr = True
                    bind_new_dr_to_item = True
                    new_dr = other_dr
                    error_fixed = True
        except:
            found = False
        
        if not found:
            #Ищем в файловой системе внутри хранилища
            need_break = False
            for root, dirs, files in os.walk(self.repo_base_path):
                for file in files:
                    #Сначала смотрим хеш в кеше
                    hash = self.seen_files.get(os.path.join(root, file))
                    if hash is None:
                        hash = compute_hash(os.path.join(root, file))
                        self.seen_files[os.path.join(root, file)] = hash
                    if hash == item.data_ref.hash:
                        #Нужно создать новый data_ref
                        new_url = os.path.relpath(os.path.join(root, file), self.repo_base_path)
                        new_dr = DataRef(type=DataRef.FILE, url=new_url, date_created=datetime.datetime.today())
                        new_dr.hash = hash
                        new_dr.size = os.path.getsize(os.path.join(root, file))
                        self.uow.session.add(new_dr)
                        self.uow.session.flush()
                        #Удалить item.data_ref
                        #Привязать новый data_ref к item
                        delete_old_dr = True
                        bind_new_dr_to_item = True
                        error_fixed = True
                        
                        need_break = True
                        break
                if need_break:
                    break
        
        if delete_old_dr:
            rows = self.uow.session.query(DataRef).filter(DataRef.id==item.data_ref.id)\
                .delete(synchronize_session=False)
            if rows == 0:
                raise Exception("Cannot delete data_ref object.")
            elif rows > 1:
                raise Exception("The query deleted {} data_ref objects (it should delete only one).")
                    
        if bind_new_dr_to_item and new_dr is not None:
            item_0 = self.uow.session.query(Item).filter(Item.id==item.id).one()
            item_0.data_ref_id = new_dr.id
            item_0.data_ref = new_dr
            self.uow.session.flush()
            
            if item_0 in self.uow.session:
                self.uow.session.expunge(item_0)
            
            if new_dr in self.uow.session:
                self.uow.session.expunge(new_dr)
            
            try:
                self.lock.lockForWrite()
                item.data_ref = new_dr
            finally:
                self.lock.unlock()
        
        return error_fixed
             
    
    
    
    


