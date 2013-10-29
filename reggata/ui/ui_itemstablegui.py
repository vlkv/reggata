# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\itemstablegui.ui'
#
# Created: Tue Oct 29 20:36:09 2013
#      by: PyQt4 UI code generator 4.10
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_ItemsTableGui(object):
    def setupUi(self, ItemsTableGui):
        ItemsTableGui.setObjectName(_fromUtf8("ItemsTableGui"))
        ItemsTableGui.resize(528, 300)
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
        self.tableViewContainer = QtGui.QVBoxLayout()
        self.tableViewContainer.setObjectName(_fromUtf8("tableViewContainer"))
        self.verticalLayout.addLayout(self.tableViewContainer)

        self.retranslateUi(ItemsTableGui)
        QtCore.QMetaObject.connectSlotsByName(ItemsTableGui)

    def retranslateUi(self, ItemsTableGui):
        ItemsTableGui.setWindowTitle(_translate("ItemsTableGui", "Form", None))
        self.label.setText(_translate("ItemsTableGui", "Query:", None))
        self.pushButton_query_exec.setText(_translate("ItemsTableGui", "Execute", None))
        self.pushButton_query_reset.setText(_translate("ItemsTableGui", "Reset", None))
        self.label_2.setText(_translate("ItemsTableGui", "Limit:", None))
        self.spinBox_limit.setToolTip(_translate("ItemsTableGui", "Maximum number of rows per page to display (0 - no limit).", None))
        self.label_3.setText(_translate("ItemsTableGui", "Page:", None))

