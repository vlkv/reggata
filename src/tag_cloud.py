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

Created on 13.11.2010

@author: vlkv
'''
import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui
from PyQt4.QtCore import Qt
from helpers import tr, show_exc_info, DialogMode, is_none_or_empty
from parsers.query_tokens import needs_quote
from parsers.util import quote
import parsers
from exceptions import MsgException
from user_config import UserConfig

#TODO Сделать по Ctr+F поиск тега в облаке (т.к. в хранилище обычно очень много тегов)

def scale_value(value, src_range, dst_range):
    ''' Выполняет масштабирование значения value, которое может варьироваться в пределах
    от src_range[0] до src_range[1], после чего значение попадает в диапазон от dst_range[0] до 
    dst_range[1].
        Если value находится вне диапазона src_range, то оно будет сдвинуто на соответствующую
        границу.
    '''    
    if src_range[0] > src_range[1]:
        raise ValueError(tr("Incorrect range, src_range[0] must be less then src_range[1]."))
    
    if dst_range[0] > dst_range[1]:
        raise ValueError(tr("Incorrect range, dst_range[0] must be less then dst_range[1]."))
    
    result = float(value) * (float(dst_range[0]) - dst_range[1]) / (src_range[0] - src_range[1])
    if result < dst_range[0]:
        result = dst_range[0]
    elif result > dst_range[1]:
        result = dst_range[1]
    return result

class TagCloud(QtGui.QTextEdit):
    '''
    Виджет для отображения облака тегов.
    '''
    
    def __init__(self, parent=None, repo=None):
        #Current word in tag cloud under the mouse cursor
        self.word = None
        
        #This is a list of tuples (tag_name, count_of_items_with_this_tag)
        self.tag_count = None
        
        super(TagCloud, self).__init__(parent)
        self.setMouseTracking(True)
        self.setReadOnly(True)
        self.tags = set() #Выбранные теги
        self.not_tags = set() #Выбранные отрицания тегов
        self._repo = repo
        
        self.menu = None #Это ссылка на контекстное меню (при нажатии правой кнопки мыши)
        
        
        
        try:
            self._limit = int(UserConfig().get("tag_cloud.limit", 0))
            if self._limit < 0:
                raise ValueError()
        except:
            self._limit = 0
        
        #Пользователи (их логины), теги которых должны отображаться в облаке
        #Если пустое множество, то в облаке отображаются теги всех пользователей
        self._users = set() #TODO Это пока что не используется... (не реализовано)
    
        self.selection_start = 0
        self.selection_end = 0
    
    def _set_limit(self, value):
        self._limit = value
        self.refresh()
    
    def _get_limit(self):
        return self._limit
    
    limit = property(_get_limit, _set_limit)
    
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
            uow = self.repo.create_unit_of_work()
            try:
                tags = uow.get_related_tags(list(self.tags), limit=self.limit)
                
                self.tag_count = tags
                
                tags_sorted = sorted(tags, key=lambda tag : tag.c, reverse=True)
                sizes = dict()
                size_max = 6
                i = 0
                while i < size_max and i < len(tags_sorted):
                    sizes[tags_sorted[i].c] = size_max - i
                    i += 1                
                
                text = ""
                for tag in tags:
                    font_size = sizes.get(tag.c, 0)
                    
                    palette = QtGui.QApplication.palette()
                    
                    #Тут как раз НЕ нужно escape-ить имена тегов!
                    bg_color = UserConfig().get("tag_cloud.tag_background_color", palette.window().color().name())
                    fg_color = UserConfig().get("tag_cloud.tag_text_color", palette.text().color().name())
                    text = text + ' <font style="BACKGROUND-COLOR: {0}" size="+{1}" color="{2}">'.format(bg_color, font_size, fg_color) + tag.name + '</font>'
                    
                self.setText(text)
            finally:
                uow.close()

    def reset(self):
        self.tags.clear()
        self.not_tags.clear()
        self.emit(QtCore.SIGNAL("reset"))
        self.refresh()
    
    def mouseMoveEvent(self, e):
        
        #Get current word under cursor
        cursor = self.cursorForPosition(e.pos())
        cursor.select(QtGui.QTextCursor.WordUnderCursor)
        word = cursor.selectedText()        
        
        #If current word has changed (or cleared) --- set default formatting to the previous word
        if word != self.word or is_none_or_empty(word):
            cursor1 = self.textCursor()
            cursor1.setPosition(self.selection_start)
            cursor1.setPosition(self.selection_end, QtGui.QTextCursor.KeepAnchor)
            format = QtGui.QTextCharFormat()
            format.setForeground(QtGui.QBrush(Qt.black))
            cursor1.mergeCharFormat(format)
            self.word = None
        
        if word != self.word:
            self.selection_start = cursor.selectionStart()
            self.selection_end = cursor.selectionEnd()
            
            format = QtGui.QTextCharFormat()
            format.setForeground(QtGui.QBrush(Qt.blue))
            cursor.mergeCharFormat(format)
            self.word = word
        
        #TODO Если тег содержит пробелы (или другие символы, типа - (дефис)) 
        #то word неправильно определяется!
        #Надо будет что-то по этому поводу сделать
        return super(TagCloud, self).mouseMoveEvent(e)
    
    def event(self, e):
#        print(type(e), e.type())
        if e.type() == QtCore.QEvent.Enter:
            pass
        elif e.type() == QtCore.QEvent.Leave:
            #Colour previous word into default color
            cursor1 = self.textCursor()
            cursor1.setPosition(self.selection_start)
            cursor1.setPosition(self.selection_end, QtGui.QTextCursor.KeepAnchor)
            format = QtGui.QTextCharFormat()
            format.setForeground(QtGui.QBrush(Qt.black))
            cursor1.mergeCharFormat(format)
            self.word = None
        elif self.word is not None and self.tag_count is not None and e.type() == QtCore.QEvent.ToolTip:
            #Show number of items for tag name under the mouse cursor
            for tag_name, tag_count in self.tag_count:
                if tag_name == self.word:
                    QtGui.QToolTip.showText(e.globalPos(), str(tag_count))
                    break
        return super(TagCloud, self).event(e)
    
    def mouseDoubleClickEvent(self, e):
        '''Добавление тега в запрос.'''
        
        if not is_none_or_empty(self.word):
            if e.modifiers() == Qt.ControlModifier:
                self.not_tags.add(self.word)
            else:
                self.tags.add(self.word)
            self.emit(QtCore.SIGNAL("selectedTagsChanged"))
            self.refresh()
           
    
    def and_tag(self):
        '''Добавление тега в запрос (через контекстное меню).'''
        try:
            sel_text = self.textCursor().selectedText()
            if not sel_text:                
                sel_text = self.word
            if not sel_text:
                raise MsgException(self.tr("There is no selected text in tag cloud."))
            if parsers.query_parser.needs_quote(sel_text):
                sel_text = parsers.util.quote(sel_text)
            self.tags.add(sel_text)
            self.emit(QtCore.SIGNAL("selectedTagsChanged"))
            self.refresh()
        except Exception as ex:
            show_exc_info(self, ex)
        
    def and_not_tag(self):
        '''Добавление отрицания тега в запрос (через контекстное меню).'''
        try:
            sel_text = self.textCursor().selectedText()
            if not sel_text:                
                sel_text = self.word
            if not sel_text:
                raise MsgException(self.tr("There is no selected text in tag cloud."))
            if parsers.query_parser.needs_quote(sel_text):
                sel_text = parsers.util.quote(sel_text)
            self.not_tags.add(sel_text)
            self.emit(QtCore.SIGNAL("selectedTagsChanged"))
            self.refresh()
        except Exception as ex:
            show_exc_info(self, ex)
        
    def set_limit(self):
        i, ok = QtGui.QInputDialog.getInteger(self, self.tr("Reggata input dialog"), \
            self.tr("Enter new value for maximum number of tags in the cloud (0 - unlimited)."), \
            value=self.limit, min=0, max=1000000000)
        if ok:
            self.limit = i
            UserConfig().store("tag_cloud.limit", i)
    
    def contextMenuEvent(self, e):
        if not self.menu:
            self.menu = QtGui.QMenu()
            self.action_and_tag = self.menu.addAction(self.tr("AND Tag"))
            self.connect(self.action_and_tag, QtCore.SIGNAL("triggered()"), self.and_tag)
            self.action_and_not_tag = self.menu.addAction(self.tr("AND NOT Tag"))
            self.connect(self.action_and_not_tag, QtCore.SIGNAL("triggered()"), self.and_not_tag)            
            self.action_set_limit = self.menu.addAction(self.tr("Limit number of tags"))
            self.connect(self.action_set_limit, QtCore.SIGNAL("triggered()"), self.set_limit)
        self.menu.exec_(e.globalPos())        
     
 
    
    
