# -*- coding: utf-8 -*-
'''
Created on 30.11.2010

@author: vlkv
'''
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt
import ui_itemsdialog
import os
import helpers
from exceptions import MsgException
from helpers import is_internal, DialogMode, is_none_or_empty
import parsers
from db_schema import DataRef


class CustomTextEdit(QtGui.QTextEdit):
    '''Немного модифицированный QTextEdit, который отображает весь вводимый 
    пользователем текст выделяющимся шрифтом (вне зависимости от текущего 
    формата редактируемого текста).'''
    #Так как я реализовал сейчас ItemsDialog, вообще не нужно редактировать текст на CustomTextEdit-ах
    #Для ввода текста я сделал отдельные виджеты. Поэтому в __init__() стоит self.setReadOnly(True)
        
    def __init__(self, parent=None):
        super(CustomTextEdit, self).__init__(parent)
        self.setReadOnly(True)
    
    def event(self, e):
        if e.type() == QtCore.QEvent.KeyPress:
            #Делаем ввод нового текста синим шрифтом
            f = QtGui.QTextCharFormat()
            self.setCurrentCharFormat(f)
            self.setTextColor(Qt.blue)
        return super(CustomTextEdit, self).event(e)
    

class ItemsDialog(QtGui.QDialog):
    '''
    Диалог для выполнения операций над группой элементов. Очень удобно, если у 
    пользователя будет возможность добавлять элементы в хранилище группами
    (при этом ко всем добавляемым элементам привязывается одинаковый набор тегов
    и полей-значений), а также
    редактировать их (операции с тегами/полями и с физическим расположением файлов) 
    группами.
    '''
    
    

    
    

    def __init__(self, parent=None, items=[], mode=DialogMode.EDIT, same_dst_path=True):
        super(ItemsDialog, self).__init__(parent)
        self.ui = ui_itemsdialog.Ui_ItemsDialog()
        self.ui.setupUi(self)
        
        self.parent = parent
        self.items = items
        self.dst_path = None
        self.group_has_files = False
        
        #If this field is true, all items will be moved into selected destination path
        self.same_dst_path = same_dst_path
        
        
        if len(items) <= 1:
            raise ValueError(self.tr("ItemsDialog cannot operate with one or zero Item objects."))
        self.ui.label_num_of_items.setText(str(len(items)))
        
        
        self.connect(self.ui.buttonBox, QtCore.SIGNAL("accepted()"), self.button_ok)
        self.connect(self.ui.buttonBox, QtCore.SIGNAL("rejected()"), self.button_cancel)
        self.connect(self.ui.pushButton_select_dst_path, QtCore.SIGNAL("clicked()"), self.select_dst_path)
        
        
        self.ui.textEdit_tags = CustomTextEdit()
        self.ui.verticalLayout_tags.addWidget(self.ui.textEdit_tags)
        
        self.ui.textEdit_fields = CustomTextEdit()
        self.ui.verticalLayout_fields.addWidget(self.ui.textEdit_fields)
        
        
        self.set_dialog_mode(mode)
        self.read()
        
        
    
    def set_dialog_mode(self, mode):
        if mode == DialogMode.CREATE:
            self.ui.label_tags.setVisible(False)
            self.ui.textEdit_tags.setVisible(False)
            
            self.ui.label_fields.setVisible(False)
            self.ui.textEdit_fields.setVisible(False)
            
            self.ui.label_tags_rm.setVisible(False)
            self.ui.plainTextEdit_tags_rm.setVisible(False)
            
            self.ui.label_fields_rm.setVisible(False)
            self.ui.plainTextEdit_fields_rm.setVisible(False)
        elif mode == DialogMode.EDIT:
            pass
        else:
            raise ValueError(self.tr("ItemsDialog does not support DialogMode = {}.").format(mode))
        self.mode = mode    
    
    def write(self):
        
        #Если пользователь выберет другую директорию назначения, то мы ее 
        #сохраняем в поле DataRef.dst_path (это будет только имя директории!!!)
        
        if self.mode == DialogMode.EDIT and self.group_has_files and not is_none_or_empty(self.dst_path):
            for item in self.items:
                if item.data_ref and item.data_ref.type != DataRef.FILE:
                    continue
                item.data_ref.dst_path = self.dst_path
        
        elif self.mode == DialogMode.CREATE:
            for item in self.items:
                if item.data_ref and item.data_ref.type != DataRef.FILE:
                    continue                
                if self.same_dst_path:
                    item.data_ref.dst_path = self.dst_path
                else:
                    if self.dst_path:
                        item.data_ref.dst_path = os.path.normpath(os.path.join(self.dst_path, item.data_ref.dst_subpath))
                    else:
                        item.data_ref.dst_path = os.path.normpath(item.data_ref.dst_subpath)
#                        if item.data_ref.dst_path == os.curdir:
#                            item.data_ref.dst_path = ""
                
                 
        
        #Теги, которые нужно добавить        
        text = self.ui.plainTextEdit_tags_add.toPlainText()
        tags, tmp = parsers.definition_parser.parse(text)
        tags_add = set(tags)
        
        #Теги, которые нужно удалить
        text = self.ui.plainTextEdit_tags_rm.toPlainText()
        tags, tmp = parsers.definition_parser.parse(text)
        tags_rm = set(tags)
        
        #Поля, которые нужно добавить
        text = self.ui.plainTextEdit_fields_add.toPlainText()
        tmp, fields = parsers.definition_parser.parse(text)
        fieldvals_add = set(fields)
        
        #Имена полей, которые нужно удалить
        text = self.ui.plainTextEdit_fields_rm.toPlainText()
        tmp, fields = parsers.definition_parser.parse(text)
        fields_rm = set(fields) #Здесь используется парсер для тегов!
            
            
        
        #Выполняем проверку, чтобы добавляемые и удаляемые теги не пересекались
        intersection = tags_add.intersection(tags_rm)
        if len(intersection) > 0:
            raise ValueError(self.tr("Tags {} cannot be in both add and remove lists.").format(str(intersection)))
        
        #Выполняем проверку, чтобы добавляемые и удаляемые поля не пересекались
        intersection = set()
        for f, v in fieldvals_add:
            if f in fields_rm:
                intersection.add(f)
        if len(intersection) > 0:
            raise ValueError(self.tr("Fields {} cannot be in both add and remove lists.").format(str(intersection)))
            
        for item in self.items:
            #Добавляем новые теги
            for t in tags_add:
                if not item.has_tag(t):
                    item.add_tag(name=t)
            
            #Удаляем теги
            for t in tags_rm:
                item.remove_tag(t)

            #Добавляем новые поля
            for f, v in fieldvals_add:
                #Сначала удаляем
                item.remove_field(f)
                #Теперь добавляем (вдруг, значение поля изменилось?)
                item.set_field_value(f, v)
            
            #Удаляем поля
            for f in fields_rm:
                item.remove_field(f)
                    
            
        
    def read(self):
        '''Теги, которые есть у всех элементов из items нужно выводить черным.
        Теги, которые есть только у части элементов в списке items, нужно выводить
        серым (или другим отличным) цветом. Аналогично и для полей-значений. Черным
        выводить только те поля-значения, которые есть у всех элементов (причем, 
        совпадают и имя поля и значение.'''
        
        diff_values_html = self.tr("&lt;diff. values&gt;")
        
        if not (len(self.items) > 1):
            return
    
        if self.mode == DialogMode.EDIT:
        
            tags_str = ""
            seen_tags = set()
            for i in range(0, len(self.items)):
                for j in range(0, len(self.items[i].item_tags)):
                    tag_name = self.items[i].item_tags[j].tag.name
                    if tag_name in seen_tags:
                        continue
                    has_all = True
                    for k in range(0, len(self.items)):
                        if i == k:
                            continue
                        if not self.items[k].has_tag(tag_name):
                            has_all = False
                            break
                    seen_tags.add(tag_name)
                    if has_all:
                        tags_str = tags_str + "<b>" + tag_name + "</b> "
                    else:
                        tags_str = tags_str + '<font color="grey">' + tag_name + "</font> "                    
            self.ui.textEdit_tags.setText(tags_str)
            
            fields_str = ""
            seen_fields = set()
            for i in range(0, len(self.items)):
                for j in range(0, len(self.items[i].item_fields)):
                    field_name = self.items[i].item_fields[j].field.name
                    field_value = self.items[i].item_fields[j].field_value
                    if field_name in seen_fields:
                        continue
                    all_have_field = True
                    all_have_field_value = True
                    for k in range(0, len(self.items)):
                        if i == k:
                            continue
                        if not self.items[k].has_field(field_name):
                            all_have_field = False
                        if not self.items[k].has_field(field_name, field_value):
                            all_have_field_value = False
                        if not all_have_field and not all_have_field_value:
                            break
                            
                    seen_fields.add(field_name)
                    if all_have_field_value:
                        fields_str = fields_str + "<b>" + field_name + ": " + field_value + "</b><br/>"
                    elif all_have_field:
                        fields_str = fields_str + '<b>' + field_name + "</b>: " + diff_values_html + "<br/>"
                    else:
                        fields_str = fields_str + '<font color="grey">' + field_name + ": " + diff_values_html + "</font><br/>"
            self.ui.textEdit_fields.setText(fields_str)
    
    
    
            self.dst_path = None
            same_path = None
            for i in range(len(self.items)):
                #При подсчете не учитываются объекты DataRef имеющие тип URL (или любой отличный от FILE)
                #Также не учитываются элементы, которые не связаны с DataRef-объектами
                if self.items[i].data_ref is None or self.items[i].data_ref.type != DataRef.FILE:
                    continue
                
                if self.dst_path is None:
                    self.dst_path, null = os.path.split(self.items[i].data_ref.url)
                    same_path = 'yes'
                else:
                    path, null = os.path.split(self.items[i].data_ref.url)
                    if self.dst_path != path:
                        same_path = 'no'
                        break
            if same_path is None:
                #Все элементы не содержат ссылок на файлы (Либо нет DataRef объектов, либо они есть но не типа FILE)
                self.dst_path = None
                self.group_has_files = False
                self.ui.lineEdit_dst_path.setText(self.tr('<not applicable>'))
            elif same_path == 'yes':
                #Все элементы, связанные с DataRef-ами типа FILE, находятся в ОДНОЙ директории
                self.group_has_files = True
                self.ui.lineEdit_dst_path.setText(self.dst_path)
            else:
                #Элементы, связанные с DataRef-ами типа FILE, находятся в РАЗНЫХ директориях
                self.dst_path = None #Обнуляем это поле
                self.group_has_files = True
                self.ui.lineEdit_dst_path.setText(self.tr('<different values>'))
                
        elif self.mode == DialogMode.CREATE:
            pass
            
                
        
    def select_dst_path(self):
        try:
            if self.mode == DialogMode.EDIT and not self.group_has_files:
                raise MsgException(self.tr("Selected group of items doesn't reference any physical files on filesysem."))
            
            dir = QtGui.QFileDialog.getExistingDirectory(self, 
                self.tr("Select destination path within repository"), 
                self.parent.active_repo.base_path)
            if dir:
                if not is_internal(dir, self.parent.active_repo.base_path):
                    #Выбрана директория снаружи хранилища
                    raise MsgException(self.tr("Chosen directory is out of active repository."))
                else:
                    self.dst_path = os.path.relpath(dir, self.parent.active_repo.base_path)
                    self.ui.lineEdit_dst_path.setText(self.dst_path)
        
        except Exception as ex:
            helpers.show_exc_info(self, ex)
             
                            
          
    def button_ok(self):
        try:
            self.write()            
            self.accept()
        except Exception as ex:
            helpers.show_exc_info(self, ex)
    
    def button_cancel(self):
        self.reject()
        
        
                