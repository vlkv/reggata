'''
Created on 30.11.2010

@author: vlkv
'''
from PyQt4 import QtGui, QtCore
import ui_itemsdialog

class ItemsDialog(QtGui.QDialog):
    '''
    Диалог для выполнения операций над группой элементов.
    '''
    
    #TODO Диалог не доделан!

    items = None

    def __init__(self, items=[], parent=None):
        super(ItemsDialog, self).__init__(parent)
        self.ui = ui_itemsdialog.Ui_ItemsDialog()
        self.ui.setupUi(self)
        self.items = items
        
        self.connect(self.ui.buttonBox, QtCore.SIGNAL("accepted()"), self.button_ok)
        self.connect(self.ui.buttonBox, QtCore.SIGNAL("rejected()"), self.button_cancel)
        
        self.read()
        
        #TODO Добавить поддержку DialogMode
        
        
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
                    
                            
          
    def button_ok(self):        
        pass
    
    def button_cancel(self):
        self.reject()
        
        
                