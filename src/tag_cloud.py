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

Created on 13.11.2010

@author: vlkv
'''
import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui
from helpers import tr, showExcInfo, DialogMode, scale_value

class TagCloud(QtGui.QTextEdit):
    '''
    Виджет для отображения облака тегов.
    '''
    
    #Пользователи (их логины), теги которых должны отображаться в облаке
    #Если пустое множество, то в облаке отображаются теги всех пользователей
    _users = set()
    
    _repo = None
        
    
    def __init__(self, parent=None, repo=None):
        super(TagCloud, self).__init__(parent)
        self.setMouseTracking(True)
        self.setReadOnly(True)
        self.tags = set() #Выбранные теги        
        self.not_tags = set() #Выбранные отрицания тегов
        self.repo = repo        
        
    
    def add_user(self, user_login):
        self._users.add(user_login)
        self.refresh()
    
    def clear_users(self):
        self._users.clear()
        self.refresh()
        
    def remove_user(self, user_login):
        self._users.remove(user_login)
        self.refresh()
    
    @property
    def repo(self):
        return self._repo
    
    @repo.setter
    def repo(self, value):
        self._repo = value
        self.reset()
        
    
    
    def refresh(self):        
        #TODO Реализовать фильтрацию по пользователям
        user_logins = list(self._users)
        
        if self.repo is None:
            self.setText("")
        else:
            uow = self.repo.createUnitOfWork()
            try:
                tags = uow.get_related_tags(list(self.tags))
                
                #Поиск минимального и максимального количества
                min = max = 0 #Отрицательным кол-во быть не может
                for tag in tags:
                    if tag.c < min:
                        min = tag.c
                    if tag.c > max:
                        max = tag.c
                
                text = ""
                for tag in tags:
                    font_size = int(scale_value(tag.c, (min, max), (0, 5)))                    
                    text = text + ' <font size="+{}">'.format(font_size) + tag.name + '</font>'
                self.setText(text)
            finally:
                uow.close()

    def reset(self):
        self.tags.clear()
        self.not_tags.clear()
        self.emit(QtCore.SIGNAL("reset"))
        self.refresh()
    
    def mouseMoveEvent(self, e):
        cursor = self.cursorForPosition(e.pos())
        cursor.select(QtGui.QTextCursor.WordUnderCursor)
        word = cursor.selectedText()
        self.word = word
        
    def mouseDoubleClickEvent(self, e):
        #TODO Нужно при нажатом Ctr добавлять word в множество _not_tags
        if self.word != "" and self.word is not None:            
            self.tags.add(self.word)            
            self.emit(QtCore.SIGNAL("selectedTagsChanged"))
            self.refresh()
            
#    def event(self, e):        
#        print(str(e))
#        return super(TagCloud, self).event(e)