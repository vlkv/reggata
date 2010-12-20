# -*- coding: utf-8 -*-
'''
Copyright 2010 Vitaly Volkov

This file is part of Reggata.

Reggata is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Reggata is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Reggata.  If not, see <http://www.gnu.org/licenses/>.

Created on 20.12.2010

Модуль содержит классы для исправления целостности элементов хранилища.
'''
from db_schema import HistoryRec, Item, DataRef
from exceptions import NotFoundError, WrongValueError
import repo_mgr
from helpers import tr, compute_hash
import os
import datetime

class IntegrityFixer(object):
    '''Базовый класс для классов, исправляющих целостность элементов.'''
    
    @staticmethod
    def create_fixer(code, strategy, uow, repo_base_path, items_lock):
        if code == Item.ERROR_FILE_NOT_FOUND:
            return FileNotFoundFixer(strategy, uow, repo_base_path, items_lock)
        elif code == Item.ERROR_FILE_HASH_MISMATCH:
            return FileHashMismatchFixer(strategy, uow, repo_base_path, items_lock)
        elif code == Item.ERROR_HISTORY_REC_NOT_FOUND:
            return HistoryRecNotFoundFixer(strategy, uow, repo_base_path, items_lock)
        else:
            raise Exception(tr("There is no fixer class for item integrity error code {0}.").format(code))

    def code(self):
        raise NotImplementedError(tr("This is an abstract class."))
    
    def fix_error(self, item, user_login):
        raise NotImplementedError(tr("This is an abstract class."))
    
class FileNotFoundFixer(IntegrityFixer):
    TRY_FIND = 0 #Искать оригинальный файл
    TRY_FIND_ELSE_DELETE = 1 #Искать оригинальный файл, если не найден, то удалить DataRef объект
    DELETE = 2 #Удалить DataRef объект
    
    def __init__(self, strategy, uow, repo_base_path, items_lock):
        if strategy not in [self.TRY_FIND, self.TRY_FIND_ELSE_DELETE, self.DELETE]:
            raise Exception(tr("Wrong strategy value {0}").format(strategy))
        self.strategy = strategy
        self.uow = uow
        self.repo_base_path = repo_base_path
        self.lock = items_lock
    
    def code(self):
        return Item.ERROR_FILE_NOT_FOUND
    
    
        

class FileHashMismatchFixer(IntegrityFixer):
    TRY_FIND_FILE = 0 #Искать оригинальный файл
    UPDATE_HASH = 1 #Записать новое значение хеша в объект DataRef
    
    def __init__(self, strategy, uow, repo_base_path, items_lock):
        if strategy not in [self.UPDATE_HASH, self.TRY_FIND_FILE]:
            raise Exception(tr("Wrong strategy value {0}").format(strategy))
        self.strategy = strategy
        self.uow = uow
        self.repo_base_path = repo_base_path
        self.lock = items_lock
        
    def code(self):
        return Item.ERROR_FILE_HASH_MISMATCH
    
    def _try_find_file(self, item, user_login):
        #Пытаемся найти внутри хранилища файл, хеш которого совпадает с item.data_ref.hash
        #Если нашли, то привязываем item к найденному файлу. 
        #При этом либо придется отредактировать url у существующего data_ref объекта, либо 
        #привязаться к другому data_ref объекту.
        
        #Пока что делаем по простому, без кеширования и проч. Будет медленно. Но улучшать алгоритм буду потом.
        for root, dirs, files in os.walk(self.repo_base_path):
            for file in files:
                hash = compute_hash(os.path.join(root, file)
                #TODO реализовать...
             
    
    def _update_hash(self, item, user_login):
        #Вычисляем новый хеш и размер файла
        filename = os.path.join(self.repo_base_path, item.data_ref.url)
        new_hash = compute_hash(filename)
        new_size = os.path.getsize(filename)
        new_date_hashed = datetime.datetime.today()
        
        #Извлекаем копию data_ref из БД, данный объект будет принадлежать текущей сессии
        data_ref = self.uow.session.query(DataRef).get(item.data_ref.id)
        if data_ref.hash == new_hash and data_ref.size == new_size:
            raise Exception(tr("This item.data_ref already has correct hash and size values."))
        #Меняем только эти три поля!
        data_ref.hash = new_hash
        data_ref.size = new_size
        data_ref.date_hashed = new_date_hashed 
        self.uow.session.flush()
        
        #Сохраняем в историю изменений запись о том, что data_ref был модифицирован
        parent_hr = repo_mgr.UnitOfWork._find_item_latest_history_rec(self.uow.session, item)
        if parent_hr is None:
            raise Exception(tr("Please fix history rec error first."))
        hr = HistoryRec()
        hr.item_id = item.id
        hr.item_hash = item.hash()
        hr.parent1_id = parent_hr.id
        if item.data_ref is not None:
            hr.data_ref_hash = new_hash
            hr.data_ref_url = item.data_ref.url
            hr.operation = HistoryRec.UPDATE
            hr.user_login = user_login
        self.uow.session.add(hr)
        self.uow.session.flush()
        
        try:
            self.lock.lockForWrite()
            item.data_ref.hash = new_hash
            item.data_ref.size = new_size
            item.data_ref.date_hashed = new_date_hashed
        finally:
            self.lock.unlock()   
    
    def fix_error(self, item, user_login):
        
        if item.data_ref is None:
            raise Exception(tr("This item has no related files."))
        
        if self.strategy == self.UPDATE_HASH:
            self._update_hash(item, user_login)
        elif self.strategy == self.TRY_FIND_FILE:
            self._try_find_file(item, user_login)
        else:
            raise Exception(tr("Not supported strategy = {0}.").format(self.strategy))
    

class FileSizeMismatchFixer(FileHashMismatchFixer):
    #Класс по сути ничем не отличается от FileHashMismatchFixer 
    def code(self):
        return Item.ERROR_FILE_SIZE_MISMATCH

class HistoryRecNotFoundFixer(IntegrityFixer):
    TRY_PROCEED = 0 #Попытаться найти историю элемента и привязаться к ней
    TRY_PROCEED_ELSE_RENEW = 1 #Попытаться найти историю элемента и привязаться к ней, если не получится, то создать новую запись CREATE в истории
    RENEW = 2 #создать новую запись CREATE в истории изменений (как будто данный элемент был только что создан)
    
    def __init__(self, strategy, uow, repo_base_path, items_lock):
        if strategy not in [self.TRY_PROCEED, self.TRY_PROCEED_ELSE_RENEW]:
            raise Exception(tr("Wrong strategy value {0}").format(strategy))
        self.strategy = strategy
        self.uow = uow
    
    def code(self):
        return Item.ERROR_HISTORY_REC_NOT_FOUND
    
    def _renew(self, item, user_login):
        hr = HistoryRec()
        hr.item_id = item.id
        hr.item_hash = item.hash()
        if item.data_ref is not None:
            hr.data_ref_hash = item.data_ref.hash
            hr.data_ref_url = item.data_ref.url
            hr.operation = HistoryRec.CREATE
            hr.user_login = user_login
        self.uow.session.add(hr)
        self.uow.session.flush()
    
    def _try_proceed(self, item, user_login):
        parent_hr = self.uow.session.query(HistoryRec).filter(HistoryRec.item_id==item.id)\
            .order_by(HistoryRec.id.desc()).first()
            
        if parent_hr is None:
            raise NotFoundError(tr("Cannot find candidate for a parent history record."))
        
        if parent_hr.operation not in [HistoryRec.UPDATE, HistoryRec.MERGE]:
            raise WrongValueError(tr("Cannot find candidate for a parent history record."))
        
        hr = HistoryRec()
        hr.item_id = item.id
        hr.item_hash = item.hash()
        hr.parent1_id = parent_hr.id
        if item.data_ref is not None:
            hr.data_ref_hash = item.data_ref.hash
            hr.data_ref_url = item.data_ref.url
            hr.operation = HistoryRec.UPDATE
            hr.user_login = user_login
        self.uow.session.add(hr)
        self.uow.session.flush()
            
    
    def fix_error(self, item, user_login):
        hr = repo_mgr.UnitOfWork._find_item_latest_history_rec(self.uow.session, item)
        if hr is not None:
            raise Exception(tr("Item is already ok."))
        
        if self.strategy == self.RENEW:
            self._renew(item, user_login)
        elif self.strategy == self.TRY_PROCEED:
            self._try_proceed(item, user_login)
        elif self.strategy == self.TRY_PROCEED_ELSE_RENEW:
            try:
                self._try_proceed(item, user_login)
            except (NotFoundError, WrongValueError):
                self._renew(item, user_login)
        else:
            raise Exception(tr("Not supported strategy = {0}.").format(self.strategy))        
        
        


