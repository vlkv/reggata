# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'filebrowsergui.ui'
#
# Created: Sat Mar 30 15:26:52 2013
#      by: PyQt4 UI code generator 4.9.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_FileBrowserGui(object):
    def setupUi(self, FileBrowserGui):
        FileBrowserGui.setObjectName(_fromUtf8("FileBrowserGui"))
        FileBrowserGui.resize(461, 314)
        self.verticalLayout = QtGui.QVBoxLayout(FileBrowserGui)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.currDirLineEdit = QtGui.QLineEdit(FileBrowserGui)
        self.currDirLineEdit.setText(_fromUtf8(""))
        self.currDirLineEdit.setReadOnly(True)
        self.currDirLineEdit.setObjectName(_fromUtf8("currDirLineEdit"))
        self.verticalLayout.addWidget(self.currDirLineEdit)
        self.filesTableView = QtGui.QTableView(FileBrowserGui)
        self.filesTableView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.filesTableView.setObjectName(_fromUtf8("filesTableView"))
        self.filesTableView.verticalHeader().setVisible(False)
        self.verticalLayout.addWidget(self.filesTableView)

        self.retranslateUi(FileBrowserGui)
        QtCore.QMetaObject.connectSlotsByName(FileBrowserGui)

    def retranslateUi(self, FileBrowserGui):
        FileBrowserGui.setWindowTitle(QtGui.QApplication.translate("FileBrowserGui", "Form", None, QtGui.QApplication.UnicodeUTF8))

