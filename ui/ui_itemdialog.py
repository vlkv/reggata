# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'itemdialog.ui'
#
# Created: Tue Dec  7 00:24:15 2010
#      by: PyQt4 UI code generator 4.8.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_ItemDialog(object):
    def setupUi(self, ItemDialog):
        ItemDialog.setObjectName(_fromUtf8("ItemDialog"))
        ItemDialog.resize(513, 454)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ItemDialog.sizePolicy().hasHeightForWidth())
        ItemDialog.setSizePolicy(sizePolicy)
        ItemDialog.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.verticalLayout_2 = QtGui.QVBoxLayout(ItemDialog)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.lineEdit_id = QtGui.QLineEdit(ItemDialog)
        self.lineEdit_id.setReadOnly(True)
        self.lineEdit_id.setObjectName(_fromUtf8("lineEdit_id"))
        self.gridLayout.addWidget(self.lineEdit_id, 0, 2, 1, 1)
        self.lineEdit_user_login = QtGui.QLineEdit(ItemDialog)
        self.lineEdit_user_login.setReadOnly(True)
        self.lineEdit_user_login.setObjectName(_fromUtf8("lineEdit_user_login"))
        self.gridLayout.addWidget(self.lineEdit_user_login, 0, 5, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 0, 6, 1, 1)
        self.label_2 = QtGui.QLabel(ItemDialog)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 2)
        self.lineEdit_title = QtGui.QLineEdit(ItemDialog)
        self.lineEdit_title.setObjectName(_fromUtf8("lineEdit_title"))
        self.gridLayout.addWidget(self.lineEdit_title, 1, 2, 1, 5)
        self.label = QtGui.QLabel(ItemDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 1, 1, 1)
        self.label_5 = QtGui.QLabel(ItemDialog)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.gridLayout.addWidget(self.label_5, 0, 3, 1, 1)
        self.verticalLayout_2.addLayout(self.gridLayout)
        self.verticalLayout_4 = QtGui.QVBoxLayout()
        self.verticalLayout_4.setObjectName(_fromUtf8("verticalLayout_4"))
        self.label_3 = QtGui.QLabel(ItemDialog)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.verticalLayout_4.addWidget(self.label_3)
        self.plainTextEdit_notes = QtGui.QPlainTextEdit(ItemDialog)
        self.plainTextEdit_notes.setMinimumSize(QtCore.QSize(0, 46))
        self.plainTextEdit_notes.setObjectName(_fromUtf8("plainTextEdit_notes"))
        self.verticalLayout_4.addWidget(self.plainTextEdit_notes)
        self.verticalLayout_2.addLayout(self.verticalLayout_4)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label_4 = QtGui.QLabel(ItemDialog)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.verticalLayout.addWidget(self.label_4)
        self.listWidget_data_refs = QtGui.QListWidget(ItemDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.listWidget_data_refs.sizePolicy().hasHeightForWidth())
        self.listWidget_data_refs.setSizePolicy(sizePolicy)
        self.listWidget_data_refs.setMinimumSize(QtCore.QSize(0, 46))
        self.listWidget_data_refs.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.listWidget_data_refs.setObjectName(_fromUtf8("listWidget_data_refs"))
        self.verticalLayout.addWidget(self.listWidget_data_refs)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.pushButton_add_files = QtGui.QPushButton(ItemDialog)
        self.pushButton_add_files.setObjectName(_fromUtf8("pushButton_add_files"))
        self.horizontalLayout.addWidget(self.pushButton_add_files)
        self.pushButton_add_URL = QtGui.QPushButton(ItemDialog)
        self.pushButton_add_URL.setObjectName(_fromUtf8("pushButton_add_URL"))
        self.horizontalLayout.addWidget(self.pushButton_add_URL)
        self.pushButton_remove = QtGui.QPushButton(ItemDialog)
        self.pushButton_remove.setObjectName(_fromUtf8("pushButton_remove"))
        self.horizontalLayout.addWidget(self.pushButton_remove)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        self.horizontalLayout_5 = QtGui.QHBoxLayout()
        self.horizontalLayout_5.setObjectName(_fromUtf8("horizontalLayout_5"))
        self.label_8 = QtGui.QLabel(ItemDialog)
        self.label_8.setObjectName(_fromUtf8("label_8"))
        self.horizontalLayout_5.addWidget(self.label_8)
        self.lineEdit_dst_path = QtGui.QLineEdit(ItemDialog)
        self.lineEdit_dst_path.setReadOnly(True)
        self.lineEdit_dst_path.setObjectName(_fromUtf8("lineEdit_dst_path"))
        self.horizontalLayout_5.addWidget(self.lineEdit_dst_path)
        self.pushButton_select_dst_path = QtGui.QPushButton(ItemDialog)
        self.pushButton_select_dst_path.setObjectName(_fromUtf8("pushButton_select_dst_path"))
        self.horizontalLayout_5.addWidget(self.pushButton_select_dst_path)
        self.verticalLayout_2.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_4 = QtGui.QHBoxLayout()
        self.horizontalLayout_4.setObjectName(_fromUtf8("horizontalLayout_4"))
        self.verticalLayout_7 = QtGui.QVBoxLayout()
        self.verticalLayout_7.setObjectName(_fromUtf8("verticalLayout_7"))
        self.label_7 = QtGui.QLabel(ItemDialog)
        self.label_7.setObjectName(_fromUtf8("label_7"))
        self.verticalLayout_7.addWidget(self.label_7)
        self.plainTextEdit_fields = QtGui.QPlainTextEdit(ItemDialog)
        self.plainTextEdit_fields.setMinimumSize(QtCore.QSize(0, 46))
        self.plainTextEdit_fields.setObjectName(_fromUtf8("plainTextEdit_fields"))
        self.verticalLayout_7.addWidget(self.plainTextEdit_fields)
        self.horizontalLayout_4.addLayout(self.verticalLayout_7)
        self.verticalLayout_8 = QtGui.QVBoxLayout()
        self.verticalLayout_8.setObjectName(_fromUtf8("verticalLayout_8"))
        self.label_6 = QtGui.QLabel(ItemDialog)
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.verticalLayout_8.addWidget(self.label_6)
        self.plainTextEdit_tags = QtGui.QPlainTextEdit(ItemDialog)
        self.plainTextEdit_tags.setMinimumSize(QtCore.QSize(0, 46))
        self.plainTextEdit_tags.setObjectName(_fromUtf8("plainTextEdit_tags"))
        self.verticalLayout_8.addWidget(self.plainTextEdit_tags)
        self.horizontalLayout_4.addLayout(self.verticalLayout_8)
        self.verticalLayout_2.addLayout(self.horizontalLayout_4)
        self.buttonBox = QtGui.QDialogButtonBox(ItemDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout_2.addWidget(self.buttonBox)

        self.retranslateUi(ItemDialog)
        QtCore.QMetaObject.connectSlotsByName(ItemDialog)

    def retranslateUi(self, ItemDialog):
        ItemDialog.setWindowTitle(QtGui.QApplication.translate("ItemDialog", "Repository item", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("ItemDialog", "Title:", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("ItemDialog", "Id:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(QtGui.QApplication.translate("ItemDialog", "User:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("ItemDialog", "Notes:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("ItemDialog", "Data references:", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_add_files.setText(QtGui.QApplication.translate("ItemDialog", "Add files", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_add_URL.setText(QtGui.QApplication.translate("ItemDialog", "Add URLs", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_remove.setText(QtGui.QApplication.translate("ItemDialog", "Remove", None, QtGui.QApplication.UnicodeUTF8))
        self.label_8.setText(QtGui.QApplication.translate("ItemDialog", "Destination path:", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_select_dst_path.setText(QtGui.QApplication.translate("ItemDialog", "Select", None, QtGui.QApplication.UnicodeUTF8))
        self.label_7.setText(QtGui.QApplication.translate("ItemDialog", "Fields:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_6.setText(QtGui.QApplication.translate("ItemDialog", "Tags:", None, QtGui.QApplication.UnicodeUTF8))

