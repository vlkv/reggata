# -*- coding: utf-8 -*-
'''
Created on 21.01.2012

@author: vlkv
'''
import consts
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt
import traceback
from db_schema import Item, DataRef
import os
from parsers import query_parser
from worker_threads import ThumbnailBuilderThread
from repo_mgr import *
from commands import *

class RepoItemTableModel(QtCore.QAbstractTableModel):
    '''
    This class is a model of a table (QTableView) with repository Items.
    '''
    
    ID = 0
    TITLE = 1
    IMAGE_THUMB = 2
    LIST_OF_TAGS = 3
    STATE = 4 #State of the item (in the means of its integrity)
    RATING = 5
    
    def __init__(self, repo, items_lock, user_login):
        super(RepoItemTableModel, self).__init__()
        self.repo = repo
        self.items = []
        self._user_login = user_login
        
        
        #This is a thread for building image thumbnails in the background
        self.thread = None
        
        #This is a lock to synchronize threads, reading/writing to self.items collection
        self.lock = items_lock

        self.query_text = ""
        self.limit = 0
        self.page = 1
        
        self.order_by_column = None
        self.order_dir = None


    def reset_single_row(self, row):
        topL = self.createIndex(row, self.ID)
        bottomR = self.createIndex(row, self.RATING)
        self.emit(QtCore.SIGNAL("dataChanged(const QModelIndex&, const QModelIndex&)"), topL, bottomR)

    def _set_user_login(self, user_login):
        self._user_login = user_login
        
    def _get_user_login(self):
        return self._user_login
        
    user_login = property(_get_user_login, _set_user_login, doc="Current active user login.")
    
    
    def sort(self, column, order=Qt.AscendingOrder):
        if column not in [self.ID, self.TITLE, self.RATING]:
            return
        
        self.order_by_column = column
        self.order_dir = order
                
        self.query(self.query_text, self.limit, self.page)
        
    def query(self, query_text, limit=0, page=1):
        '''Выполняет извлечение элементов из хранилища.'''
        
        self.query_text = query_text
        self.limit = limit
        self.page = page
        
        if self.order_dir == Qt.AscendingOrder:
            dir = "ASC"
        else:
            dir = "DESC"
        
        order_by = []        
        if self.order_by_column is not None:
            column = self.order_by_column
            if column == self.ID:
                order_by.append(("id", dir))                
            elif column == self.TITLE:
                order_by.append(("title", dir))
            #This is not exactly sorting by pure rating, but by fields and their values...
            elif column == self.RATING:
                order_by.append(("items_fields_field_id", "DESC"))
                order_by.append(("items_fields_field_value", dir))
    
        
        def reset_row(row):
            self.reset_single_row(row)
            QtCore.QCoreApplication.processEvents()
        
        uow = self.repo.create_unit_of_work()
        try:
            #Нужно остановить поток (запущенный от предыдущего запроса), если будет выполнен новый запрос (этот)
            if self.thread is not None and self.thread.isRunning():
                #Нужно остановить поток, если будет выполнен другой запрос
                self.thread.interrupt = True
                self.thread.wait(5*1000) #TODO Тут может надо ждать бесконечно?
                        
            if query_text is None or query_text.strip()=="":
                #Если запрос пустой, тогда извлекаем элементы не имеющие тегов
                self.items = uow.executeCommand(GetUntaggedItems(limit, page, order_by))
            else:
                query_tree = query_parser.parse(query_text)
                cmd = QueryItemsByParseTree(query_tree, limit, page, order_by)
                self.items = uow.executeCommand(cmd)
            
            #Нужно запустить поток, который будет генерировать миниатюры
            self.thread = ThumbnailBuilderThread(self, self.repo, self.items, self.lock)
            self.connect(self.thread, QtCore.SIGNAL("progress"), lambda percents, row: reset_row(row))            
            self.thread.start()
                
            self.reset()
        finally:
            uow.close()
    
        
                
        
    
    def rowCount(self, index=QtCore.QModelIndex()):
        return len(self.items)
    
    def columnCount(self, index=QtCore.QModelIndex()):
        return 6
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                if section == self.ID:
                    return self.tr("Id")
                elif section == self.TITLE:
                    return self.tr("Title")
                elif section == self.IMAGE_THUMB:
                    return self.tr("Thumbnail")
                elif section == self.LIST_OF_TAGS:
                    return self.tr("Tags")
                elif section == self.STATE:
                    return self.tr("State")
                elif section == self.RATING:
                    return self.tr("Rating")
            else:
                return None
        elif orientation == Qt.Vertical and role == Qt.DisplayRole:
            return section + 1
        else:
            return None

    
    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self.items)):
            return None
        
        item = self.items[index.row()]
        column = index.column()
        
        if role == QtCore.Qt.DisplayRole:
            if column == self.ID:
                return item.id
            
            elif column == self.TITLE:
                return "<b>" + item.title + "</b>" + ("<br/><font>" + item.data_ref.url + "</font>" if item.data_ref else "")
            
            elif column == self.LIST_OF_TAGS:
                return item.format_tags()
            
            elif column == self.STATE:
                try:
                    self.lock.lockForRead()
                    return Item.format_error_set_short(item.error)
                finally:
                    self.lock.unlock()
            elif column == self.RATING:
                #Should display only rating field owned by current active user
                rating_str = item.get_field_value(consts.RATING_FIELD, self.user_login)
                try:
                    rating = int(rating_str)
                except:
                    rating = 0
                return rating
        
        elif role == Qt.ToolTipRole:            
            if column == self.TITLE:
                if item.data_ref is not None:
                    s  =  str(item.data_ref.type) + ": " + item.data_ref.url
                    if  item.data_ref.type == DataRef.FILE:
                        s += os.linesep + self.tr("Checksum (hash): {}").format(item.data_ref.hash)
                        s += os.linesep + self.tr("File size: {} bytes").format(item.data_ref.size)
                        s += os.linesep + self.tr("Date hashed: {}").format(item.data_ref.date_hashed)
                    s += os.linesep + self.tr("Created by: {}").format(item.data_ref.user_login)
                    s += os.linesep + self.tr("Date created: {}").format(item.data_ref.date_created)
                    
                    
                    return s
            elif column == self.LIST_OF_TAGS:
                return item.format_field_vals()
            elif column == self.STATE:
                try:
                    self.lock.lockForRead()
                    return Item.format_error_set(item.error)
                finally:
                    self.lock.unlock()
            

        #Данная роль используется для отображения миниатюр графических файлов
        elif role == QtCore.Qt.UserRole:
            if column == self.IMAGE_THUMB and item.data_ref is not None:
                if item.data_ref.is_image():
                    pixmap = QtGui.QPixmap()
                    try:                    
                        self.lock.lockForRead()
                        if len(item.data_ref.thumbnails) > 0:
                            pixmap.loadFromData(item.data_ref.thumbnails[0].data)
                    except Exception:
                        traceback.format_exc()
                    finally:
                        self.lock.unlock()
                    return pixmap
        

        elif role == QtCore.Qt.TextAlignmentRole:
            if column == self.ID:
                return int(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            elif column == self.TITLE:
                return int(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        
        #Во всех остальных случаях возвращаем None
        return None
    
    def flags(self, index):
        default_flags = super(RepoItemTableModel, self).flags(index)
        
        if index.column() == self.RATING:
            return Qt.ItemFlags(default_flags | QtCore.Qt.ItemIsEditable)             
        else:
            return default_flags
    
    def setData(self, index, value, role=QtCore.Qt.EditRole):
        
        if role == Qt.EditRole and index.column() == self.RATING:
            item = self.items[index.row()]
            
            #Remember old rating value
            old_value = item.get_field_value(consts.RATING_FIELD, self.user_login)
            
            if old_value == value:
                return False
            
            item.set_field_value(consts.RATING_FIELD, value, self.user_login)
            
            #Store new rating value into database
            uow = self.repo.create_unit_of_work()
            try:
                cmd = UpdateExistingItemCommand(item, self.user_login)
                uow.executeCommand(cmd)
                self.emit(QtCore.SIGNAL("dataChanged(const QModelIndex&, const QModelIndex&)"), index, index)
                return True
            except:
                #Restore old value
                item.set_field_value(consts.RATING_FIELD, old_value, self.user_login)
            finally:
                uow.close()
        
        return False
