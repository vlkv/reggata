# -*- coding: utf-8 -*-
'''
Created on 15.10.2010

@author: vlkv
'''
import PyQt4.QtGui as qtgui
import PyQt4.QtCore as qtcore
import ui_itemdialog
from db_model import Item, DataRef, Tag, Item_Tag, Field, Item_Field,\
    Item_DataRef
from helpers import tr, showExcInfo, DialogMode, index_of, is_none_or_empty
import os

class ItemDialog(qtgui.QDialog):
    '''
    Диалог для представления одного элемента хранилища
    '''

    def __init__(self, item, parent=None, mode=DialogMode.VIEW):
        super(ItemDialog, self).__init__(parent)
        if type(item) != Item:
            raise TypeError(self.tr("Argument item should be an instance of Item class."))
        #if type(parent) != MainWindow: #Не получается сделать import модуля с этим классом!!!
        #    raise TypeError(self.tr("Parent must be an instance of MainWindow class."))
            #Это нужно для получения доступа к полю active_repo главного окна, например
        self.parent = parent
        self.mode = mode
        self.item = item
        self.ui = ui_itemdialog.Ui_ItemDialog()
        self.ui.setupUi(self)
        self.connect(self.ui.buttonBox, qtcore.SIGNAL("accepted()"), self.button_ok)
        self.connect(self.ui.buttonBox, qtcore.SIGNAL("rejected()"), self.button_cancel)
        self.connect(self.ui.pushButton_add_files, qtcore.SIGNAL("clicked()"), self.button_add_files)
        self.connect(self.ui.pushButton_remove, qtcore.SIGNAL("clicked()"), self.button_remove)
        self.connect(self.ui.pushButton_select_dst_path, qtcore.SIGNAL("clicked()"), self.button_sel_dst_path)
        self.read()
        
    
    def read(self):
        self.ui.lineEdit_id.setText(str(self.item.id))
        self.ui.lineEdit_user_login.setText(self.item.user_login)
        self.ui.lineEdit_title.setText(self.item.title)
        self.ui.plainTextEdit_notes.setPlainText(self.item.notes)
                
        for idr in self.item.item_data_refs:
            it = qtgui.QListWidgetItem(idr.data_ref.url)
            self.ui.listWidget_data_refs.addItem(it)
            
        s = ""
        for itf in self.item.item_fields:
            s = s + itf.field.name + "=" + itf.field_value + os.linesep
        self.ui.plainTextEdit_fields.setPlainText(s)
        
        s = ""
        for itg in self.item.item_tags:
            s = s + itg.tag.name + " "
        self.ui.plainTextEdit_tags.setPlainText(s)
    
        #TODO остальные поля?
        
    
    def write(self):
        '''Запись введенной в элементы gui информации в поля объекта.'''
        self.item.title = self.ui.lineEdit_title.text()
        self.item.notes = self.ui.plainTextEdit_notes.toPlainText()
        
        #Создаем объекты Tag
        text = self.ui.plainTextEdit_tags.toPlainText()
        for t in text.split():
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
        
        #TODO ...
        
        
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
                
                #Метод write() создаст все необходимые теги/поля
                self.write()
                self.item.check_valid()
                self.accept()
                                
        except Exception as ex:
            showExcInfo(self, ex)
    
    def button_cancel(self):
        self.reject()
        
    def button_add_files(self):
        files = qtgui.QFileDialog.getOpenFileNames(self, self.tr("Select files to add"))
        for file in files:
            #Если lineEdit для title еще пустой, то предлагаем туда записать имя первого файла
            title = self.ui.lineEdit_title.text()
            if is_none_or_empty(title):
                self.ui.lineEdit_title.setText(os.path.basename(file))
            
            #Создаем DataRef объект и привязываем его к self.item
            idr = Item_DataRef(DataRef(url=file, type="FILE"))
            idr.data_ref.dst_path = self.ui.lineEdit_dst_path.text()
            self.item.item_data_refs.append(idr)
                        
            #Отображаем в списке файлов диалога
            list_item = qtgui.QListWidgetItem(file)
            self.ui.listWidget_data_refs.addItem(list_item)
            
    
    def button_sel_dst_path(self):
        dir = qtgui.QFileDialog.getExistingDirectory(self, 
            self.tr("Select destination path in repository"), 
            self.parent.active_repo.base_path)
        if dir:
            commonprefix = os.path.commonprefix([dir, self.parent.active_repo.base_path])
            if commonprefix != self.parent.active_repo.base_path:
                qtgui.QMessageBox.warning(self, self.tr("Error"), self.tr("Chosen directory is out of active repository."))
                return
            else:
                new_dst_path = os.path.relpath(dir, self.parent.active_repo.base_path)
                self.ui.lineEdit_dst_path.setText(new_dst_path)
                #Присваиваем новое значение dst_path всем объектам DataRef, кроме
                #тех, которые уже расположены внутри хранилища
                for idr in self.item.item_data_refs:                    
                    drive, tail = os.path.splitdrive(idr.data_ref.url)
                    if tail.startswith(os.sep):
                        #Этот файл еще не в хранилище
                        idr.data_ref.dst_path = new_dst_path 
    
    def button_remove(self):
        if self.ui.listWidget_data_refs.count() == 0:
            return
        
        sel_items = self.ui.listWidget_data_refs.selectedItems()
        for list_item in sel_items:
            row = self.ui.listWidget_data_refs.row(list_item)
            self.ui.listWidget_data_refs.takeItem(row)
            
            #Если такой элемент есть в объекте Item, то удаляем его 
            i = index_of(self.item.item_data_refs, lambda x: True if x.data_ref.url == list_item.text() else False)
            if i is not None:
                self.item.item_data_refs.remove(self.item.item_data_refs[i])
            
            
            
            
            
            
            
            
            
            
            
            
            
        