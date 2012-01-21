'''
Created on 21.01.2012

@author: vlkv
'''
import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui
from PyQt4.QtCore import Qt

import ui_itemstabledockwidget
import helpers
from user_config import UserConfig

class ItemsTableDockWidget(QtGui.QDockWidget):
    
    def __init__(self, parent):
        super(ItemsTableDockWidget, self).__init__(parent)
        self.ui = ui_itemstabledockwidget.Ui_ItemsTableDockWidget()
        self.ui.setupUi(self)
        
        #Widgets for text queries
        self.ui.lineEdit_query = helpers.TextEdit(self, one_line=True)
        tmp = QtGui.QHBoxLayout(self.ui.widget_lineEdit_query)
        tmp.addWidget(self.ui.lineEdit_query)        
        self.connect(self.ui.pushButton_query_exec, QtCore.SIGNAL("clicked()"), self.query_exec)
        self.connect(self.ui.lineEdit_query, QtCore.SIGNAL("returnPressed()"), self.ui.pushButton_query_exec.click)
        self.connect(self.ui.pushButton_query_reset, QtCore.SIGNAL("clicked()"), self.query_reset)
        
        #TODO limit page function sometimes works not correct!!! It sometimes shows less items, than specified in limit spinbox!
        #Initialization of limit and page spinboxes 
        self.ui.spinBox_limit.setValue(int(UserConfig().get("spinBox_limit.value", 0)))
        self.ui.spinBox_limit.setSingleStep(int(UserConfig().get("spinBox_limit.step", 5)))
        self.connect(self.ui.spinBox_limit, QtCore.SIGNAL("valueChanged(int)"), self.query_exec)
        self.connect(self.ui.spinBox_limit, QtCore.SIGNAL("valueChanged(int)"), lambda: UserConfig().store("spinBox_limit.value", self.ui.spinBox_limit.value()))
        self.connect(self.ui.spinBox_limit, QtCore.SIGNAL("valueChanged(int)"), lambda val: self.ui.spinBox_page.setEnabled(val > 0))
        self.connect(self.ui.spinBox_page, QtCore.SIGNAL("valueChanged(int)"), self.query_exec)
        self.ui.spinBox_page.setEnabled(self.ui.spinBox_limit.value() > 0)
    
    def query_exec(self):
        self.emit(QtCore.SIGNAL("query_exec"))
    
    def query_reset(self):
        self.emit(QtCore.SIGNAL("query_reset"))
    
    def addContextMenu(self, menu):
        self.ui.tableView_items.setContextMenuPolicy(Qt.CustomContextMenu)
        self.connect(self.ui.tableView_items, QtCore.SIGNAL("customContextMenuRequested(const QPoint &)"), self.showContextMenu)
    
    def showContextMenu(self, pos):
        self.menu.exec_(self.ui.tableView_items.mapToGlobal(pos))
        
    def setTableModel(self, model):
        self.ui.tableView_items.setModel(model)
        