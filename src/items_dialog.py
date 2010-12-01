'''
Created on 30.11.2010

@author: vlkv
'''
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt
import ui_itemsdialog
import os


class CustomTextEdit(QtGui.QTextEdit):
    '''Немного модифицированный QTextEdit, который отображает весь вводимый 
    пользователем текст выделяющимся шрифтом (вне зависимости от текущего 
    формата редактируемого текста).'''
    def __init__(self, parent=None):
        super(CustomTextEdit, self).__init__(parent)
        
    def currentCharFormatChanged(self, fmt):
        print("currentCharFormatChanged()")
        old_fmt = self.currentCharFormat()
        self.setCurrentCharFormat(old_fmt)
    
    def event(self, e):
        print(str(e))
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
    
    #TODO Диалог не доделан!

    items = None

    dst_path = None

    def __init__(self, items=[], parent=None):
        super(ItemsDialog, self).__init__(parent)
        self.ui = ui_itemsdialog.Ui_ItemsDialog()
        self.ui.setupUi(self)
        self.items = items
        
        self.connect(self.ui.buttonBox, QtCore.SIGNAL("accepted()"), self.button_ok)
        self.connect(self.ui.buttonBox, QtCore.SIGNAL("rejected()"), self.button_cancel)
        
        self.ui.textEdit_tags = CustomTextEdit()
        self.ui.verticalLayout_tags.addWidget(self.ui.textEdit_tags)
        
        self.ui.textEdit_fields = CustomTextEdit()
        self.ui.verticalLayout_fields.addWidget(self.ui.textEdit_fields)
        
        self.read()
        
        #TODO Добавить поддержку DialogMode
    
    def write(self):
        self.dst_path = self.ui.lineEdit_dst_path.text()
        
    def read(self):
        '''Теги, которые есть у всех элементов из items нужно выводить черным.
        Теги, которые есть только у части элементов в списке items, нужно выводить
        серым (или другим отличным) цветом. Аналогично и для полей-значений. Черным
        выводить только те поля-значения, которые есть у всех элементов (причем, 
        совпадают и имя поля и значение.'''
        
        if not (len(self.items) > 1):
            return
    
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
                    fields_str = fields_str + "<b>" + field_name + ": " + field_value + "</b> "
                elif all_have_field:
                    fields_str = fields_str + '<b>' + field_name + "</b>: ### "
                    #TODO Могут быть проблемы, если значением тега реально будет строка '###'
                else:
                    fields_str = fields_str + '<font color="grey">' + field_name + "</font>: ### "
        self.ui.textEdit_fields.setText(fields_str)



        self.dst_path = None
        same_path = None
        for i in range(len(self.items)):
            if self.items[i].data_ref is None or self.items[i].data_ref.type != 'FILE':
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
            #Все элементы не содержат ссылок на файлы
            self.dst_path = None
            self.ui.lineEdit_dst_path.setText(self.tr('<not applicable>'))
        elif same_path == 'yes':
            #Все элементы, связанные с DataRef-ами типа FILE, находятся в ОДНОЙ директории
            self.ui.lineEdit_dst_path.setText(self.dst_path)
        else:
            #Элементы, связанные с DataRef-ами типа FILE, находятся в РАЗНЫХ директориях
            self.dst_path = None #Обнуляем это поле
            self.ui.lineEdit_dst_path.setText(self.tr('<different values>'))
        
        #При подсчете не учитываются объекты DataRef имеющие тип URL (или любой отличный от FILE)        
        
                
             
                            
          
    def button_ok(self):        
        pass
    
    def button_cancel(self):
        self.reject()
        
        
                