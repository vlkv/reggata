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

Created on 15.10.2010

@author: vlkv
'''
import PyQt4.QtGui as QtGui
import PyQt4.QtCore as QtCore
import ui_itemdialog
from db_model import Item, DataRef, Tag, Item_Tag, Field, Item_Field
from helpers import tr, showExcInfo, DialogMode, index_of, is_none_or_empty,\
    is_internal
import os
from parsers import tags_def_parser

class ItemDialog(QtGui.QDialog):
    '''
    Диалог для представления одного элемента хранилища
    '''

    def __init__(self, item, parent=None, mode=DialogMode.VIEW):
        super(ItemDialog, self).__init__(parent)
        if type(item) != Item:
            raise TypeError(self.tr("Argument item should be an instance of Item class."))

        #parent обязательно должен быть экземпляром MainWindow
        #потому, что дальше будут обращения к полю parent.active_repo 
        if parent.__class__.__name__ != "MainWindow": 
            raise TypeError(self.tr("Parent must be an instance of MainWindow class."))
            
        self.parent = parent
        self.mode = mode
        self.item = item
        self.ui = ui_itemdialog.Ui_ItemDialog()
        self.ui.setupUi(self)
        self.connect(self.ui.buttonBox, QtCore.SIGNAL("accepted()"), self.button_ok)
        self.connect(self.ui.buttonBox, QtCore.SIGNAL("rejected()"), self.button_cancel)
        self.connect(self.ui.pushButton_add_files, QtCore.SIGNAL("clicked()"), self.button_add_files)
        self.connect(self.ui.pushButton_remove, QtCore.SIGNAL("clicked()"), self.button_remove)
        self.connect(self.ui.pushButton_select_dst_path, QtCore.SIGNAL("clicked()"), self.button_sel_dst_path)
        self.read()
        
    
    def read(self):
        self.ui.lineEdit_id.setText(str(self.item.id))
        self.ui.lineEdit_user_login.setText(self.item.user_login)
        self.ui.lineEdit_title.setText(self.item.title)
        self.ui.plainTextEdit_notes.setPlainText(self.item.notes)
        
        #Добавляем в список единственный файл
        if self.item.data_ref:
            #TODO если файл --- это архив, то на лету распаковать его и вывести в этот список все содержимое архива
            lwitem = QtGui.QListWidgetItem(self.item.data_ref.url)
            self.ui.listWidget_data_refs.addItem(lwitem)        
            #Проверяем, существует ли файл
            test_url = self.item.data_ref.url
            if not os.path.isabs(test_url):
                test_url = self.parent.active_repo.base_path + os.sep + test_url
            if not os.path.exists(test_url):
                lwitem.setTextColor(QtCore.Qt.red)
        
        #Выводим информацию о полях элемента и их значениях
        s = ""
        for itf in self.item.item_fields:
            s = s + itf.field.name + "=" + itf.field_value + os.linesep
        self.ui.plainTextEdit_fields.setPlainText(s)
        
        #Выводим список тегов данного элемента
        s = ""
        for itg in self.item.item_tags:
            s = s + itg.tag.name + " "
        self.ui.plainTextEdit_tags.setPlainText(s)
        
    
    def write(self):
        '''Запись введенной в элементы gui информации в поля объекта.'''
        self.item.title = self.ui.lineEdit_title.text()
        self.item.notes = self.ui.plainTextEdit_notes.toPlainText()
        
        #Создаем объекты Tag
        text = self.ui.plainTextEdit_tags.toPlainText()
        for t in tags_def_parser.parse(text):
            tag = Tag(name=t)
            item_tag = Item_Tag(tag)
            item_tag.user_login = self.item.user_login
            self.item.item_tags.append(item_tag)
        #TODO сделать поддержку двойных кавычек
        
        #Создаем объекты Field
        text = self.ui.plainTextEdit_fields.toPlainText()
        for pair in text.split():
            f, v = pair.split('=')
            field = Field(name=f)
            item_field = Item_Field(field, v)
            item_field.user_login = self.item.user_login
            self.item.item_fields.append(item_field)
        
        
        
        
    def button_ok(self):
        try:
            if self.mode == DialogMode.VIEW:
                self.accept()
                
            elif self.mode == DialogMode.CREATE:
                self.write()
                self.item.check_valid()
                self.accept()
                
            elif self.mode == DialogMode.EDIT:
                #Очищаем коллекции тегов/полей
                del self.item.item_tags[:]
                del self.item.item_fields[:]
                
                #Метод write() создаст все необходимые теги/поля (как бы заново)
                self.write()
                self.item.check_valid()
                self.accept()
                                
        except Exception as ex:
            showExcInfo(self, ex)
    
    def button_cancel(self):
        self.reject()
        
    def button_add_files(self):
        
        #Пока что эта кнопка будет менять текущий DataRef на другой файл.
        #В будущем можно сделать выбор файлов и добавление их в архив, с которым связан данный Item
        
        file = QtGui.QFileDialog.getOpenFileName(self, self.tr("Select file"))
        if is_none_or_empty(file):
            return
        #Если lineEdit для title еще пустой, то предлагаем туда записать имя первого файла
        title = self.ui.lineEdit_title.text()
        if is_none_or_empty(title):
            self.ui.lineEdit_title.setText(os.path.basename(file))
            
        #Создаем DataRef объект и привязываем его к self.item
        data_ref = DataRef(url=file, type="FILE")
        data_ref.dst_path = self.ui.lineEdit_dst_path.text()
        self.item.data_ref = data_ref
                        
        #Отображаем в списке файлов диалога
        self.ui.listWidget_data_refs.clear() #Удаляем все файлы, что есть сейчас
        lwitem = QtGui.QListWidgetItem(file) #Создаем и
        self.ui.listWidget_data_refs.addItem(lwitem) #добавляем новый файл в список
        
    
    def button_sel_dst_path(self):
        dir = QtGui.QFileDialog.getExistingDirectory(self, 
            self.tr("Select destination path within repository"), 
            self.parent.active_repo.base_path)
        if dir:
            if not is_internal(dir, self.parent.active_repo.base_path):
                #Выбрана директория снаружи хранилища
                QtGui.QMessageBox.warning(self, self.tr("Error"), self.tr("Chosen directory is out of active repository."))
                return
            else:
                new_dst_path = os.path.relpath(dir, self.parent.active_repo.base_path)
                self.ui.lineEdit_dst_path.setText(new_dst_path)
                #Присваиваем новое значение dst_path объекту DataRef, если он ссылается
                #на новый внешний файл (его путь абсолютный и вне хранилища)                
                if os.path.isabs(self.item.data_ref.url) and \
                not is_internal(self.item.data_ref.url, self.parent.active_repo.base_path):
                    #Этот файл еще не в хранилище
                    self.item.data_ref.dst_path = new_dst_path
    
    def button_remove(self):
        if self.ui.listWidget_data_refs.count() == 0:
            return
        
#        sel_items = self.ui.listWidget_data_refs.selectedItems()
#        for list_item in sel_items:
#            row = self.ui.listWidget_data_refs.row(list_item)
#            self.ui.listWidget_data_refs.takeItem(row)
        self.item.data_ref = None
        self.item.data_ref_id = None
        self.ui.listWidget_data_refs.clear()
            
            
            
            
            
            
            
            
            
            
            
            
            
            
        