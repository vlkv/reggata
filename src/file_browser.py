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
import helpers
from sqlalchemy import orm
from helpers import HTMLDelegate
import consts
from commands import GetFileInfoCommand, FileInfo


class FileBrowser(QtGui.QTableView):
    '''
    '''
    #TODO File browser should allow edit tags and fields

    def __init__(self, parent=None):
        super(FileBrowser, self).__init__(parent)        
        self.setModel(FileBrowserTableModel(self))
        self.setItemDelegate(HTMLDelegate(self))
        
        
    def mouseDoubleClickEvent(self, event):
        index = self.indexAt(event.pos())
        self.root_path = self.model().file_infos[index.row()].full_path
        
    def keyPressEvent(self, event):        
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            index = self.selectionModel().currentIndex()            
            self.root_path = self.model().file_infos[index.row()].full_path
        else:
            super(FileBrowser, self).keyPressEvent(event)

    def _get_root_path(self):
        return self.model().root_path
    
    def _set_root_path(self, path):
        if os.path.isdir(path) and self.model() is not None:
            self.model().root_path = path
        self.resizeRowsToContents()
        
    root_path = property(_get_root_path, _set_root_path)
    
    
    def _set_repo(self, repo):
        self.model().repo = repo
    repo = property(fset=_set_repo)
    
    

    




        
        
        
class FileBrowserTableModel(QtCore.QAbstractTableModel):
    '''A table model for displaying files (not items) of repository.'''
    
    FILENAME = 0
    TAGS = 1
    USERS = 2
    STATUS = 3
    RATING = 4
    
    def __init__(self, parent, repo=None, user_login=None):
        super(FileBrowserTableModel, self).__init__(parent)
        self._repo = repo
        self._user_login = user_login
        self.file_infos = []
        if repo is not None:
            self._root_path = repo.base_path
            self._read_root_path()

    def _set_root_path(self, value):
        
        if value is not None:        
            if self.repo is None:
                raise Exception(self.tr("Cannot set root_path, because self.repo is None."))
            
            if not helpers.is_internal(value, self.repo.base_path):
                raise Exception(self.tr("Path must be inside current repository."))
        
        self._root_path = value
        self._read_root_path()
        
    def _get_root_path(self):
        return self._root_path

    root_path = property(_get_root_path, _set_root_path, doc="root_path is just "
                         "a current directory of file browser.")

    def _set_repo(self, value):
        self._repo = value
        if value is not None:
            self.root_path = value.base_path
        else:
            self.root_path = None
            
    def _get_repo(self):
        return self._repo
    
    repo = property(_get_repo, _set_repo)
     

    def _read_root_path(self):
        
        # TODO: if there are a lot of files in repo root
        # This function is called always on start, even when file browser is hidden
        # Have to make it more lazy
        
        self.file_infos = []
        
        if self.repo is None or self.root_path is None:
            return
        
        listdir = []
        if os.path.normpath(self._root_path) != os.path.normpath(self.repo.base_path):
            listdir.append(os.pardir)
        for fname in os.listdir(self._root_path):
            listdir.append(fname)            
        
        #TODO do this in a separate thread
        uow = self.repo.create_unit_of_work()
        try:
            for fname in listdir:
                if os.path.isfile(os.path.join(self._root_path, fname)):
                    try:
                        cmd = GetFileInfoCommand(os.path.relpath(os.path.join(self._root_path, fname), self.repo.base_path))
                        finfo = uow.executeCommand(cmd)
                    except (orm.exc.NoResultFound, orm.exc.MultipleResultsFound):
                        finfo = FileInfo(self._root_path, fname, status=FileInfo.UNTRACKED_STATUS)
                else:
                    finfo = FileInfo(self._root_path, fname)
                self.file_infos.append(finfo)
                        
        finally:
            uow.close()
            
        self.reset()

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
                if finfo.type == FileInfo.DIR:                
                    return "<b>" + finfo.filename + "</b>"
                else:
                    return finfo.filename
            elif column == self.TAGS:
                return helpers.to_commalist(finfo.tags(), lambda x: x, " ")
            elif column == self.USERS:
                return helpers.to_commalist(finfo.users(), lambda x: x, " ")
            elif column == self.STATUS:
                return finfo.status
            elif column == self.RATING:
                #Should display only rating field owned by current active user
                rating_str = finfo.get_field_value(consts.RATING_FIELD, self.user_login)
                try:
                    rating = int(rating_str)
                except:
                    rating = 0
                stars = ""
                for i in range(rating):
                    stars += '\u2605'
#Also:
#U+2605 BLACK STAR
#U+2606 WHITE STAR
#U+1F44D THUMBS UP SIGN
#U+1F44E THUMBS DOWN SIGN
#U+2639 WHITE FROWNING FACE
#U+263A WHITE SMILING FACE
                return stars
      
        #return None in all other cases    
        return None
    
   