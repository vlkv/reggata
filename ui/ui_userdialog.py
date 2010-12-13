# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'userdialog.ui'
#
# Created: Mon Dec 13 08:29:20 2010
#      by: PyQt4 UI code generator 4.8.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_UserDialog(object):
    def setupUi(self, UserDialog):
        UserDialog.setObjectName(_fromUtf8("UserDialog"))
        UserDialog.resize(329, 194)
        self.verticalLayout = QtGui.QVBoxLayout(UserDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label_login = QtGui.QLabel(UserDialog)
        self.label_login.setObjectName(_fromUtf8("label_login"))
        self.gridLayout.addWidget(self.label_login, 0, 0, 1, 1)
        self.lineEdit_login = QtGui.QLineEdit(UserDialog)
        self.lineEdit_login.setObjectName(_fromUtf8("lineEdit_login"))
        self.gridLayout.addWidget(self.lineEdit_login, 0, 2, 1, 1)
        self.label_password = QtGui.QLabel(UserDialog)
        self.label_password.setObjectName(_fromUtf8("label_password"))
        self.gridLayout.addWidget(self.label_password, 1, 0, 1, 2)
        self.lineEdit_password = QtGui.QLineEdit(UserDialog)
        self.lineEdit_password.setEchoMode(QtGui.QLineEdit.Password)
        self.lineEdit_password.setObjectName(_fromUtf8("lineEdit_password"))
        self.gridLayout.addWidget(self.lineEdit_password, 1, 2, 1, 1)
        self.label_group = QtGui.QLabel(UserDialog)
        self.label_group.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.label_group.setObjectName(_fromUtf8("label_group"))
        self.gridLayout.addWidget(self.label_group, 3, 0, 1, 2)
        self.comboBox_group = QtGui.QComboBox(UserDialog)
        self.comboBox_group.setObjectName(_fromUtf8("comboBox_group"))
        self.comboBox_group.addItem(_fromUtf8(""))
        self.comboBox_group.addItem(_fromUtf8(""))
        self.gridLayout.addWidget(self.comboBox_group, 3, 2, 1, 1)
        self.label_password_repeat = QtGui.QLabel(UserDialog)
        self.label_password_repeat.setObjectName(_fromUtf8("label_password_repeat"))
        self.gridLayout.addWidget(self.label_password_repeat, 2, 0, 1, 1)
        self.lineEdit_password_repeat = QtGui.QLineEdit(UserDialog)
        self.lineEdit_password_repeat.setEchoMode(QtGui.QLineEdit.Password)
        self.lineEdit_password_repeat.setObjectName(_fromUtf8("lineEdit_password_repeat"))
        self.gridLayout.addWidget(self.lineEdit_password_repeat, 2, 2, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.buttonBox = QtGui.QDialogButtonBox(UserDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(UserDialog)
        QtCore.QMetaObject.connectSlotsByName(UserDialog)

    def retranslateUi(self, UserDialog):
        UserDialog.setWindowTitle(QtGui.QApplication.translate("UserDialog", "Repository user", None, QtGui.QApplication.UnicodeUTF8))
        self.label_login.setText(QtGui.QApplication.translate("UserDialog", "Login:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_password.setText(QtGui.QApplication.translate("UserDialog", "Password:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_group.setText(QtGui.QApplication.translate("UserDialog", "Group:", None, QtGui.QApplication.UnicodeUTF8))
        self.comboBox_group.setItemText(0, QtGui.QApplication.translate("UserDialog", "USER", None, QtGui.QApplication.UnicodeUTF8))
        self.comboBox_group.setItemText(1, QtGui.QApplication.translate("UserDialog", "ADMIN", None, QtGui.QApplication.UnicodeUTF8))
        self.label_password_repeat.setText(QtGui.QApplication.translate("UserDialog", "Repeat password:", None, QtGui.QApplication.UnicodeUTF8))

