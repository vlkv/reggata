'''
Created on 15.10.2010

@author: vlkv
'''
import PyQt4.QtGui as qtgui
import PyQt4.QtCore as qtcore
import ui_itemdialog
from db_model import Item, DataRef
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
        self.connect(self.ui.pushButton_add_files, qtcore.SIGNAL("clicked()"), self.button_add_files)
        self.connect(self.ui.pushButton_remove, qtcore.SIGNAL("clicked()"), self.button_remove)
    
    def read(self):
        '''Считывает введенную в ui элементы информацию и записывает ее в объект.'''
        self.item.title = self.ui.lineEdit_title.text()
        self.item.notes = self.ui.plainTextEdit_notes.toPlainText()
                
#        file = self.ui.listWidget_data_refs.takeItem(1)
#        while file != 0:
#            dr = DataRef()
#            dr.url = file.text()
#            self.item.data_refs.append(dr)
#            file = self.ui.listWidget_data_refs.takeItem(1)
            
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
        
    def button_add_files(self):
        files = qtgui.QFileDialog.getOpenFileNames(self, tr("Выберите файлы"))
        for file in files:
            self.ui.listWidget_data_refs.addItem(file)
            
    def button_remove(self):
        if self.ui.listWidget_data_refs.count() == 0:
            return
        
        files = self.ui.listWidget_data_refs.selectedItems()
        for file in files:
            row = self.ui.listWidget_data_refs.row(file)
            self.ui.listWidget_data_refs.takeItem(row)
        
        