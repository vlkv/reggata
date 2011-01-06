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

Created on 06.01.2011

@author: vlkv
'''

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt
import os

class FileBrowser(QtGui.QTableView):
    '''
    '''

    def __init__(self, parent=None):
        super(FileBrowser, self).__init__(parent)
        self.setModel(FileBrowserTableModel(self))
        
    def mouseDoubleClickEvent(self, event):
        index = self.indexAt(event.pos())
        self.root_path = self.model().file_infos[index.row()].full_path()
        
    def keyPressEvent(self, event):        
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            index = self.selectionModel().currentIndex()            
            self.root_path = self.model().file_infos[index.row()].full_path()
        else:
            super(FileBrowser, self).keyPressEvent(event)
    
    

    def _set_root_path(self, path):
        if os.path.isdir(path) and self.model() is not None:
            self.model().root_path = path
    
    root_path = property(fset=_set_root_path)

class FileInfo(object):
    FILE = 0
    DIR = 1
    OTHER = 2
    
    def __init__(self, path, parent_dir=False):
        
        if parent_dir:
            self.path = path
            self.filename = os.pardir
        else:
            #remove trailing slashes in this
            while path.endswith(os.sep):
                path = path[0:-1]
            self.path, self.filename = os.path.split(path)
        
        #Determine type of this path
        if os.path.isdir(path):
            self.type = self.DIR
        elif os.path.isfile(path):
            self.type = self.FILE
        else:
            self.type = self.OTHER            
        
        self.tags = set() #All tags (of all users?), linked to this item
        self.users = set() #All users (their logins), who has items linked to this file
        self.status = None
        
    def full_path(self):
        return os.path.join(self.path, self.filename)
        
class FileBrowserTableModel(QtCore.QAbstractTableModel):
    '''A table model for displaying files (not items) of repository.'''
    
    FILENAME = 0
    TAGS = 1
    USERS = 2
    STATUS = 3
    RATING = 4
    
    def __init__(self, parent, repo=None, user_login=None):
        super(FileBrowserTableModel, self).__init__(parent)
        self.repo = repo
        self._user_login = user_login
        self.file_infos = []
        if repo is not None:
            self._root_path = repo.base_path
            self._read_root_path()

    def _set_root_path(self, value):
        
        path = os.path.normpath(value)
        print("normalized path " + path)
        
        self._root_path = value
        self._read_root_path()
        
    def _get_root_path(self):
        return self._root_path

    root_path = property(_get_root_path, _set_root_path, doc="root_path is just "
                         "a current directory of file browser.")

    def _read_root_path(self):
        self.file_infos = []
        if self._root_path != self.repo.base_path:
            self.file_infos.append(FileInfo(self._root_path, parent_dir=True))
        for fname in os.listdir(self._root_path):
            self.file_infos.append(FileInfo(os.path.join(self._root_path, fname)))
        self.reset()
            
        #TODO populate information about tags, users and status of every file 

    def reset_single_row(self, row):
        topL = self.createIndex(row, self.FILENAME)
        bottomR = self.createIndex(row, self.RATING)
        self.emit(QtCore.SIGNAL("dataChanged(const QModelIndex&, const QModelIndex&)"), topL, bottomR)

    def _set_user_login(self, user_login):
        self._user_login = user_login
        
    def _get_user_login(self):
        return self._user_login
    
    user_login = property(_get_user_login, _set_user_login, doc="Current active user login.")
    
    def rowCount(self, index=QtCore.QModelIndex()):
        return len(self.file_infos)
    
    def columnCount(self, index=QtCore.QModelIndex()):
        return 5
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                if section == self.FILENAME:
                    return self.tr("Filename")
                elif section == self.TAGS:
                    return self.tr("Tags")
                elif section == self.USERS:
                    return self.tr("Users")
                elif section == self.STATUS:
                    return self.tr("Status")
                elif section == self.RATING:
                    return self.tr("Rating")
            else:
                return None
        elif orientation == Qt.Vertical and role == Qt.DisplayRole:
            return section + 1
        else:
            return None

    
    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self.file_infos)):
            return None
                
        column = index.column()
        row = index.row()
        finfo = self.file_infos[row]
        
        if role == QtCore.Qt.DisplayRole:
            if column == self.FILENAME:
                return finfo.filename
      
        #Во всех остальных случаях возвращаем None    
        return None
    
   