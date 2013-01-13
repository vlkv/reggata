# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'filebrowsergui.ui'
#
# Created: Sun Jan 13 10:46:36 2013
#      by: PyQt4 UI code generator 4.9
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
        FileBrowserGui.resize(320, 240)
        self.verticalLayout = QtGui.QVBoxLayout(FileBrowserGui)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.filesTableView = QtGui.QTableView(FileBrowserGui)
        self.filesTableView.setObjectName(_fromUtf8("filesTableView"))
        self.filesTableView.verticalHeader().setVisible(False)
        self.verticalLayout.addWidget(self.filesTableView)

        self.retranslateUi(FileBrowserGui)
        QtCore.QMetaObject.connectSlotsByName(FileBrowserGui)

    def retranslateUi(self, FileBrowserGui):
        FileBrowserGui.setWindowTitle(QtGui.QApplication.translate("FileBrowserGui", "Form", None, QtGui.QApplication.UnicodeUTF8))

