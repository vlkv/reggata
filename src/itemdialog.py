'''
Created on 15.10.2010

@author: vlkv
'''
import PyQt4.QtGui as qtgui
import PyQt4.QtCore as qtcore
import ui_itemdialog
from db_model import Item
from translator_helper import tr

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
    
    def read(self):
        '''Считывает введенную в ui элементы информацию и записывает ее в объект.'''
        self.item.title = self.ui.lineEdit_title.text()
        self.item.notes = self.ui.plainTextEdit_notes.toPlainText()
        #TODO ...
        
    def button_ok(self):
        try:
            self.read()
            self.item.check_valid()
            self.accept()
        except Exception as ex:
            qtgui.QMessageBox.warning(self, tr("Ошибка"), tr(str(ex)))
    
    def button_cancel(self):
        self.reject()
        
        
        