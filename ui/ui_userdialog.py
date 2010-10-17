# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'userdialog.ui'
#
# Created: Sun Oct 17 19:08:38 2010
#      by: PyQt4 UI code generator 4.7.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_UserDialog(object):
    def setupUi(self, UserDialog):
        UserDialog.setObjectName("UserDialog")
        UserDialog.resize(304, 138)
        self.verticalLayout = QtGui.QVBoxLayout(UserDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.splitter = QtGui.QSplitter(UserDialog)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.label = QtGui.QLabel(self.splitter)
        self.label.setObjectName("label")
        self.lineEdit_login = QtGui.QLineEdit(self.splitter)
        self.lineEdit_login.setObjectName("lineEdit_login")
        self.verticalLayout.addWidget(self.splitter)
        self.splitter_2 = QtGui.QSplitter(UserDialog)
        self.splitter_2.setOrientation(QtCore.Qt.Horizontal)
        self.splitter_2.setObjectName("splitter_2")
        self.label_2 = QtGui.QLabel(self.splitter_2)
        self.label_2.setObjectName("label_2")
        self.lineEdit_password = QtGui.QLineEdit(self.splitter_2)
        self.lineEdit_password.setEchoMode(QtGui.QLineEdit.Password)
        self.lineEdit_password.setObjectName("lineEdit_password")
        self.verticalLayout.addWidget(self.splitter_2)
        self.splitter_5 = QtGui.QSplitter(UserDialog)
        self.splitter_5.setOrientation(QtCore.Qt.Horizontal)
        self.splitter_5.setObjectName("splitter_5")
        self.label_5 = QtGui.QLabel(self.splitter_5)
        self.label_5.setObjectName("label_5")
        self.comboBox_group = QtGui.QComboBox(self.splitter_5)
        self.comboBox_group.setObjectName("comboBox_group")
        self.comboBox_group.addItem("")
        self.comboBox_group.addItem("")
        self.verticalLayout.addWidget(self.splitter_5)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.buttonBox = QtGui.QDialogButtonBox(UserDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(UserDialog)
        QtCore.QMetaObject.connectSlotsByName(UserDialog)

    def retranslateUi(self, UserDialog):
        UserDialog.setWindowTitle(QtGui.QApplication.translate("UserDialog", "Пользователь хранилища", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("UserDialog", "Логин:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("UserDialog", "Пароль:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(QtGui.QApplication.translate("UserDialog", "Группа:", None, QtGui.QApplication.UnicodeUTF8))
        self.comboBox_group.setItemText(0, QtGui.QApplication.translate("UserDialog", "USER", None, QtGui.QApplication.UnicodeUTF8))
        self.comboBox_group.setItemText(1, QtGui.QApplication.translate("UserDialog", "ADMIN", None, QtGui.QApplication.UnicodeUTF8))

