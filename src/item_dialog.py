# -*- coding: utf-8 -*-
'''
Created on 15.10.2010

@author: vlkv
'''
import PyQt4.QtGui as qtgui
import PyQt4.QtCore as qtcore
import ui_itemdialog
from db_model import Item, DataRef, Tag
from helpers import tr, showExcInfo
import os
import hashlib
import sys
import traceback

class ItemDialog(qtgui.QDialog):
    '''
    Диалог для представления одного элемента хранилища
    '''


    def __init__(self, item, parent=None):
        super(ItemDialog, self).__init__(parent)
        if type(item) != Item:
            raise TypeError(tr("Параметр item должен быть экземпляром Item."))
        self.item = item
        self.ui = ui_itemdialog.Ui_ItemDialog()
        self.ui.setupUi(self)
        self.connect(self.ui.buttonBox, qtcore.SIGNAL("accepted()"), self.button_ok)
        self.connect(self.ui.buttonBox, qtcore.SIGNAL("rejected()"), self.button_cancel)
        self.connect(self.ui.pushButton_add_files, qtcore.SIGNAL("clicked()"), self.button_add_files)
        self.connect(self.ui.pushButton_remove, qtcore.SIGNAL("clicked()"), self.button_remove)
        self.update_ui()
        
        #TODO Нужно дать пользователю возможность указать, в какую директорию положить 
        #файлы данного элемента внутри хранилища?
        #А можно просто делать директорию по именю первого тега и копировать туда?
    
    def update_ui(self):
        self.ui.lineEdit_id.setText(self.item.id)
        self.ui.lineEdit_user_login.setText(self.item.user_login)
        
        #TODO остальные поля
        
    
    def write(self):
        '''Запись введенной в элементы gui информации в поля объекта.'''
        self.item.title = self.ui.lineEdit_title.text()
        self.item.notes = self.ui.plainTextEdit_notes.toPlainText()
        
        #Создаем объекты DataRef
        for i in range(0, self.ui.listWidget_data_refs.count()):
            list_item = self.ui.listWidget_data_refs.item(i)
            dr = DataRef()
            dr.url = list_item.text()
            if list_item.data_ref_type == "file":
                dr.size = os.path.getsize(list_item.text())
                dr.type = "FILE"
            elif list_item.data_ref_type == "url":
                dr.size = 0
                dr.type = "URL"
            else:
                raise ValueError(tr("Недопустимое значение переменной ") + list_item.data_ref_type)
            #TODO вычислить hash от содержимого файла и hash_date
            dr.order_by_key = i
            dr.user_login = self.item.user_login
            self.item.data_refs.append(dr)
        
        #Создаем объекты Tag    
        text = self.ui.plainTextEdit_tags.toPlainText()
        for t in text.split():
            tag = Tag()
            tag.name = t
            tag.user_login = self.item.user_login
            self.item.tags.append(tag)
        
        
        #TODO ...
        
        
    def button_ok(self):
        try:
            self.write()
            self.item.check_valid()
            self.accept()
        except Exception as ex:
            showExcInfo(self, ex)
    
    def button_cancel(self):
        self.reject()
        
    def button_add_files(self):
        files = qtgui.QFileDialog.getOpenFileNames(self, tr("Выберите файлы"))
        for file in files:
            it = qtgui.QListWidgetItem(file)
            it.data_ref_type = "file"
            self.ui.listWidget_data_refs.addItem(it)
            
    def button_remove(self):
        if self.ui.listWidget_data_refs.count() == 0:
            return
        
        files = self.ui.listWidget_data_refs.selectedItems()
        for file in files:
            row = self.ui.listWidget_data_refs.row(file)
            self.ui.listWidget_data_refs.takeItem(row)
        
        