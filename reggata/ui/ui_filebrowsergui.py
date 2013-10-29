# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\filebrowsergui.ui'
#
# Created: Tue Oct 29 20:36:08 2013
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
        self.tableViewContainer = QtGui.QVBoxLayout()
        self.tableViewContainer.setObjectName(_fromUtf8("tableViewContainer"))
        self.verticalLayout.addLayout(self.tableViewContainer)

        self.retranslateUi(FileBrowserGui)
        QtCore.QMetaObject.connectSlotsByName(FileBrowserGui)

    def retranslateUi(self, FileBrowserGui):
        FileBrowserGui.setWindowTitle(_translate("FileBrowserGui", "Form", None))

