# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'itemsdialog.ui'
#
# Created: Sun Dec  5 12:10:28 2010
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
        ItemsDialog.resize(490, 332)
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
        self.label_fields = QtGui.QLabel(ItemsDialog)
        self.label_fields.setObjectName(_fromUtf8("label_fields"))
        self.verticalLayout_fields.addWidget(self.label_fields)
        self.horizontalLayout.addLayout(self.verticalLayout_fields)
        self.verticalLayout_tags = QtGui.QVBoxLayout()
        self.verticalLayout_tags.setObjectName(_fromUtf8("verticalLayout_tags"))
        self.label_tags = QtGui.QLabel(ItemsDialog)
        self.label_tags.setObjectName(_fromUtf8("label_tags"))
        self.verticalLayout_tags.addWidget(self.label_tags)
        self.horizontalLayout.addLayout(self.verticalLayout_tags)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.verticalLayout_fields_2 = QtGui.QVBoxLayout()
        self.verticalLayout_fields_2.setObjectName(_fromUtf8("verticalLayout_fields_2"))
        self.label_9 = QtGui.QLabel(ItemsDialog)
        self.label_9.setObjectName(_fromUtf8("label_9"))
        self.verticalLayout_fields_2.addWidget(self.label_9)
        self.plainTextEdit_fields_add = QtGui.QPlainTextEdit(ItemsDialog)
        self.plainTextEdit_fields_add.setObjectName(_fromUtf8("plainTextEdit_fields_add"))
        self.verticalLayout_fields_2.addWidget(self.plainTextEdit_fields_add)
        self.horizontalLayout_2.addLayout(self.verticalLayout_fields_2)
        self.verticalLayout_tags_2 = QtGui.QVBoxLayout()
        self.verticalLayout_tags_2.setObjectName(_fromUtf8("verticalLayout_tags_2"))
        self.label_10 = QtGui.QLabel(ItemsDialog)
        self.label_10.setObjectName(_fromUtf8("label_10"))
        self.verticalLayout_tags_2.addWidget(self.label_10)
        self.plainTextEdit_tags_add = QtGui.QPlainTextEdit(ItemsDialog)
        self.plainTextEdit_tags_add.setObjectName(_fromUtf8("plainTextEdit_tags_add"))
        self.verticalLayout_tags_2.addWidget(self.plainTextEdit_tags_add)
        self.horizontalLayout_2.addLayout(self.verticalLayout_tags_2)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.verticalLayout_fields_3 = QtGui.QVBoxLayout()
        self.verticalLayout_fields_3.setObjectName(_fromUtf8("verticalLayout_fields_3"))
        self.label_fields_rm = QtGui.QLabel(ItemsDialog)
        self.label_fields_rm.setObjectName(_fromUtf8("label_fields_rm"))
        self.verticalLayout_fields_3.addWidget(self.label_fields_rm)
        self.plainTextEdit_fields_rm = QtGui.QPlainTextEdit(ItemsDialog)
        self.plainTextEdit_fields_rm.setObjectName(_fromUtf8("plainTextEdit_fields_rm"))
        self.verticalLayout_fields_3.addWidget(self.plainTextEdit_fields_rm)
        self.horizontalLayout_3.addLayout(self.verticalLayout_fields_3)
        self.verticalLayout_tags_3 = QtGui.QVBoxLayout()
        self.verticalLayout_tags_3.setObjectName(_fromUtf8("verticalLayout_tags_3"))
        self.label_tags_rm = QtGui.QLabel(ItemsDialog)
        self.label_tags_rm.setObjectName(_fromUtf8("label_tags_rm"))
        self.verticalLayout_tags_3.addWidget(self.label_tags_rm)
        self.plainTextEdit_tags_rm = QtGui.QPlainTextEdit(ItemsDialog)
        self.plainTextEdit_tags_rm.setObjectName(_fromUtf8("plainTextEdit_tags_rm"))
        self.verticalLayout_tags_3.addWidget(self.plainTextEdit_tags_rm)
        self.horizontalLayout_3.addLayout(self.verticalLayout_tags_3)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
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
        self.label_fields.setText(QtGui.QApplication.translate("ItemsDialog", "Fields:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_tags.setText(QtGui.QApplication.translate("ItemsDialog", "Tags:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_9.setText(QtGui.QApplication.translate("ItemsDialog", "Fields to add:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_10.setText(QtGui.QApplication.translate("ItemsDialog", "Tags to add:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_fields_rm.setText(QtGui.QApplication.translate("ItemsDialog", "Field names to remove:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_tags_rm.setText(QtGui.QApplication.translate("ItemsDialog", "Tags to remove:", None, QtGui.QApplication.UnicodeUTF8))

