# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'itemstablegui.ui'
#
# Created: Wed Dec 19 19:06:12 2012
#      by: PyQt4 UI code generator 4.8.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_ItemsTableGui(object):
    def setupUi(self, ItemsTableGui):
        ItemsTableGui.setObjectName(_fromUtf8("ItemsTableGui"))
        ItemsTableGui.resize(499, 300)
        ItemsTableGui.setAcceptDrops(True)
        self.verticalLayout = QtGui.QVBoxLayout(ItemsTableGui)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.label = QtGui.QLabel(ItemsTableGui)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout.addWidget(self.label)
        self.widget_lineEdit_query = QtGui.QWidget(ItemsTableGui)
        self.widget_lineEdit_query.setObjectName(_fromUtf8("widget_lineEdit_query"))
        self.horizontalLayout.addWidget(self.widget_lineEdit_query)
        self.pushButton_query_exec = QtGui.QPushButton(ItemsTableGui)
        self.pushButton_query_exec.setObjectName(_fromUtf8("pushButton_query_exec"))
        self.horizontalLayout.addWidget(self.pushButton_query_exec)
        self.pushButton_query_reset = QtGui.QPushButton(ItemsTableGui)
        self.pushButton_query_reset.setObjectName(_fromUtf8("pushButton_query_reset"))
        self.horizontalLayout.addWidget(self.pushButton_query_reset)
        self.label_2 = QtGui.QLabel(ItemsTableGui)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.horizontalLayout.addWidget(self.label_2)
        self.spinBox_limit = QtGui.QSpinBox(ItemsTableGui)
        self.spinBox_limit.setMaximum(1000000)
        self.spinBox_limit.setSingleStep(20)
        self.spinBox_limit.setObjectName(_fromUtf8("spinBox_limit"))
        self.horizontalLayout.addWidget(self.spinBox_limit)
        self.label_3 = QtGui.QLabel(ItemsTableGui)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.horizontalLayout.addWidget(self.label_3)
        self.spinBox_page = QtGui.QSpinBox(ItemsTableGui)
        self.spinBox_page.setMinimum(1)
        self.spinBox_page.setMaximum(1000000)
        self.spinBox_page.setObjectName(_fromUtf8("spinBox_page"))
        self.horizontalLayout.addWidget(self.spinBox_page)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.tableView_items = QtGui.QTableView(ItemsTableGui)
        self.tableView_items.setDragDropMode(QtGui.QAbstractItemView.NoDragDrop)
        self.tableView_items.setDefaultDropAction(QtCore.Qt.IgnoreAction)
        self.tableView_items.setObjectName(_fromUtf8("tableView_items"))
        self.tableView_items.verticalHeader().setVisible(False)
        self.verticalLayout.addWidget(self.tableView_items)

        self.retranslateUi(ItemsTableGui)
        QtCore.QMetaObject.connectSlotsByName(ItemsTableGui)

    def retranslateUi(self, ItemsTableGui):
        ItemsTableGui.setWindowTitle(QtGui.QApplication.translate("ItemsTableGui", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("ItemsTableGui", "Query:", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_query_exec.setText(QtGui.QApplication.translate("ItemsTableGui", "Execute", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_query_reset.setText(QtGui.QApplication.translate("ItemsTableGui", "Reset", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("ItemsTableGui", "Limit:", None, QtGui.QApplication.UnicodeUTF8))
        self.spinBox_limit.setToolTip(QtGui.QApplication.translate("ItemsTableGui", "Maximum number of rows per page to display (0 - no limit).", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("ItemsTableGui", "Page:", None, QtGui.QApplication.UnicodeUTF8))
