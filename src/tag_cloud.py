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
from helpers import tr, show_exc_info, DialogMode, scale_value, is_none_or_empty
from parsers.query_tokens import needs_quote
from parsers.util import quote
import parsers
from exceptions import MsgException
from user_config import UserConfig

#TODO Сделать по Ctr+F поиск тега в облаке (т.к. в хранилище обычно очень много тегов)

class TagCloud(QtGui.QTextEdit):
    '''
    Виджет для отображения облака тегов.
    '''
    
    def __init__(self, parent=None, repo=None):
        super(TagCloud, self).__init__(parent)
        self.setMouseTracking(True)
        self.setReadOnly(True)
        self.tags = set() #Выбранные теги
        self.not_tags = set() #Выбранные отрицания тегов
        self._repo = repo
        
        self.menu = None #Это ссылка на контекстное меню (при нажатии правой кнопки мыши)
        
        #True, когда нажата клавиша Control
        self.control_pressed = False
        
        #Пользователи (их логины), теги которых должны отображаться в облаке
        #Если пустое множество, то в облаке отображаются теги всех пользователей
        self._users = set() #TODO Это пока что не используется... (не реализовано)
        
        #Значения по умолчанию
        self.hint_width = 320
        self.hint_height = 240
        
#        #Таймер для задержки отправки сигнала maySaveSize
#        self.save_state_timer = QtCore.QTimer(self)
#        self.save_state_timer.setSingleShot(True)
#        self.connect(self.save_state_timer, QtCore.SIGNAL("timeout()"), lambda: self.emit(QtCore.SIGNAL("maySaveSize")))
        
        
#    def resizeEvent(self, resize_event):
#        self.hint_width = self.width()
#        self.hint_height = self.height()
#        self.save_state_timer.start(3000)
#        #Через три секунды будет отправлен сигнал главному окну, чтобы оно 
#        #сохранило размер облака тегов
#        
#        #Как правило, если dock_widget внутри которого находится облако тегов
#        #перетаскивать мышкой в другую область, то меняется и размер облака тегов.
#        #Соответственно, срабатывает данный обработчик и потом в главном окне
#        #сохраняется размер облака тегов и заодно и положение dock_widget-а.
#        
#        return super(TagCloud, self).resizeEvent(resize_event)
        
        
#    def sizeHint(self):
#        return QtCore.QSize(self.hint_width, self.hint_height)
    
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
                    #TODO Переделать scale_value, чтобы размер определялся не пропорционально, а в порядке
                    #очередности по количеству элементов, связанным с тегом (т.е. первое место --- тег
                    #у которого больше всех элементов, второе место --- у которого чуть меньше и т.д.)
                    font_size = int(scale_value(tag.c, (min, max), (0, 5)))
                    #Тут как раз НЕ нужно escape-ить имена тегов!
                    bg_color = UserConfig().get("tag_cloud.tag_background_color", "Beige")
                    text = text + ' <font style="BACKGROUND-COLOR: ' + bg_color + '" size="+{}">'.format(font_size) + tag.name + '</font>'
                    
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
        #TODO Если тег содержит пробелы (или другие символы, типа - (дефис)) 
        #то word неправильно определяется!
        #Надо будет что-то по этому поводу сделать
        return super(TagCloud, self).mouseMoveEvent(e)
        
    def mouseDoubleClickEvent(self, e):
        '''Добавление тега в запрос.'''
        
        if not is_none_or_empty(self.word):
            if self.control_pressed:
                self.not_tags.add(self.word)
            else:
                self.tags.add(self.word)
            self.emit(QtCore.SIGNAL("selectedTagsChanged"))
            self.refresh()
            
#    def event(self, e):
#        print("TagCloud caught event " + str(e))
#        return super(TagCloud, self).event(e)
    
    def and_tag(self):
        '''Добавление тега в запрос (через контекстное меню).'''
        try:
            sel_text = self.textCursor().selectedText()
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
                    raise MsgException(self.tr("There is no selected text in tag cloud."))
            if parsers.query_parser.needs_quote(sel_text):
                sel_text = parsers.util.quote(sel_text)
            self.not_tags.add(sel_text)
            self.emit(QtCore.SIGNAL("selectedTagsChanged"))
            self.refresh()
        except Exception as ex:
            show_exc_info(self, ex)
            
    
    def contextMenuEvent(self, e):
        if not self.menu:
            self.menu = QtGui.QMenu()
            self.action_and_tag = self.menu.addAction(self.tr("AND Tag"))
            self.connect(self.action_and_tag, QtCore.SIGNAL("triggered()"), self.and_tag)
            self.action_and_not_tag = self.menu.addAction(self.tr("AND NOT Tag"))
            self.connect(self.action_and_not_tag, QtCore.SIGNAL("triggered()"), self.and_not_tag)            
        self.menu.exec_(e.globalPos())        
     
 
    
    
