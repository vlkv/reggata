# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\userdialog.ui'
#
# Created: Tue Oct 29 20:36:10 2013
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

class Ui_UserDialog(object):
    def setupUi(self, UserDialog):
        UserDialog.setObjectName(_fromUtf8("UserDialog"))
        UserDialog.resize(274, 214)
        self.verticalLayout = QtGui.QVBoxLayout(UserDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label_login = QtGui.QLabel(UserDialog)
        self.label_login.setObjectName(_fromUtf8("label_login"))
        self.gridLayout.addWidget(self.label_login, 0, 0, 1, 2)
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
        self.gridLayout.addWidget(self.label_password_repeat, 2, 0, 1, 2)
        self.lineEdit_password_repeat = QtGui.QLineEdit(UserDialog)
        self.lineEdit_password_repeat.setEchoMode(QtGui.QLineEdit.Password)
        self.lineEdit_password_repeat.setObjectName(_fromUtf8("lineEdit_password_repeat"))
        self.gridLayout.addWidget(self.lineEdit_password_repeat, 2, 2, 1, 1)
        self.label_notice = QtGui.QLabel(UserDialog)
        self.label_notice.setWordWrap(True)
        self.label_notice.setObjectName(_fromUtf8("label_notice"))
        self.gridLayout.addWidget(self.label_notice, 4, 0, 1, 3)
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
        UserDialog.setWindowTitle(_translate("UserDialog", "Repository user", None))
        self.label_login.setText(_translate("UserDialog", "Login:", None))
        self.label_password.setText(_translate("UserDialog", "Password:", None))
        self.label_group.setText(_translate("UserDialog", "Group:", None))
        self.comboBox_group.setItemText(0, _translate("UserDialog", "USER", None))
        self.comboBox_group.setItemText(1, _translate("UserDialog", "ADMIN", None))
        self.label_password_repeat.setText(_translate("UserDialog", "Repeat password:", None))
        self.label_notice.setText(_translate("UserDialog", "Note: default user login is \"user\" with empty password.", None))

