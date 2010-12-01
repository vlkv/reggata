# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'itemsdialog.ui'
#
# Created: Wed Dec  1 10:12:38 2010
#      by: PyQt4 UI code generator 4.8.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_ItemsDialog(object):
    def setupUi(self, ItemsDialog):
        ItemsDialog.setObjectName(_fromUtf8("ItemsDialog"))
        ItemsDialog.resize(512, 298)
        self.verticalLayout = QtGui.QVBoxLayout(ItemsDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout_5 = QtGui.QHBoxLayout()
        self.horizontalLayout_5.setObjectName(_fromUtf8("horizontalLayout_5"))
        self.label_8 = QtGui.QLabel(ItemsDialog)
        self.label_8.setObjectName(_fromUtf8("label_8"))
        self.horizontalLayout_5.addWidget(self.label_8)
        self.lineEdit_dst_path = QtGui.QLineEdit(ItemsDialog)
        self.lineEdit_dst_path.setReadOnly(True)
        self.lineEdit_dst_path.setObjectName(_fromUtf8("lineEdit_dst_path"))
        self.horizontalLayout_5.addWidget(self.lineEdit_dst_path)
        self.pushButton_select_dst_path = QtGui.QPushButton(ItemsDialog)
        self.pushButton_select_dst_path.setObjectName(_fromUtf8("pushButton_select_dst_path"))
        self.horizontalLayout_5.addWidget(self.pushButton_select_dst_path)
        self.verticalLayout.addLayout(self.horizontalLayout_5)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.verticalLayout_fields = QtGui.QVBoxLayout()
        self.verticalLayout_fields.setObjectName(_fromUtf8("verticalLayout_fields"))
        self.label_7 = QtGui.QLabel(ItemsDialog)
        self.label_7.setObjectName(_fromUtf8("label_7"))
        self.verticalLayout_fields.addWidget(self.label_7)
        self.horizontalLayout.addLayout(self.verticalLayout_fields)
        self.verticalLayout_tags = QtGui.QVBoxLayout()
        self.verticalLayout_tags.setObjectName(_fromUtf8("verticalLayout_tags"))
        self.label_6 = QtGui.QLabel(ItemsDialog)
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.verticalLayout_tags.addWidget(self.label_6)
        self.horizontalLayout.addLayout(self.verticalLayout_tags)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.buttonBox = QtGui.QDialogButtonBox(ItemsDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(ItemsDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), ItemsDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), ItemsDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ItemsDialog)

    def retranslateUi(self, ItemsDialog):
        ItemsDialog.setWindowTitle(QtGui.QApplication.translate("ItemsDialog", "ItemsDialog", None, QtGui.QApplication.UnicodeUTF8))
        self.label_8.setText(QtGui.QApplication.translate("ItemsDialog", "Destination path:", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_select_dst_path.setText(QtGui.QApplication.translate("ItemsDialog", "Select", None, QtGui.QApplication.UnicodeUTF8))
        self.label_7.setText(QtGui.QApplication.translate("ItemsDialog", "Fields:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_6.setText(QtGui.QApplication.translate("ItemsDialog", "Tags:", None, QtGui.QApplication.UnicodeUTF8))

