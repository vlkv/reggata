# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'userdialog.ui'
#
# Created: Fri Nov  5 21:24:04 2010
#      by: PyQt4 UI code generator 4.7.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_UserDialog(object):
    def setupUi(self, UserDialog):
        UserDialog.setObjectName("UserDialog")
        UserDialog.resize(242, 146)
        self.verticalLayout = QtGui.QVBoxLayout(UserDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.label_login = QtGui.QLabel(UserDialog)
        self.label_login.setObjectName("label_login")
        self.gridLayout.addWidget(self.label_login, 0, 0, 1, 1)
        self.lineEdit_login = QtGui.QLineEdit(UserDialog)
        self.lineEdit_login.setObjectName("lineEdit_login")
        self.gridLayout.addWidget(self.lineEdit_login, 0, 2, 1, 1)
        self.label_password = QtGui.QLabel(UserDialog)
        self.label_password.setObjectName("label_password")
        self.gridLayout.addWidget(self.label_password, 1, 0, 1, 2)
        self.lineEdit_password = QtGui.QLineEdit(UserDialog)
        self.lineEdit_password.setEchoMode(QtGui.QLineEdit.Password)
        self.lineEdit_password.setObjectName("lineEdit_password")
        self.gridLayout.addWidget(self.lineEdit_password, 1, 2, 1, 1)
        self.label_group = QtGui.QLabel(UserDialog)
        self.label_group.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.label_group.setObjectName("label_group")
        self.gridLayout.addWidget(self.label_group, 2, 0, 1, 2)
        self.comboBox_group = QtGui.QComboBox(UserDialog)
        self.comboBox_group.setObjectName("comboBox_group")
        self.comboBox_group.addItem("")
        self.comboBox_group.addItem("")
        self.gridLayout.addWidget(self.comboBox_group, 2, 2, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
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
        UserDialog.setWindowTitle(QtGui.QApplication.translate("UserDialog", "Repository user", None, QtGui.QApplication.UnicodeUTF8))
        self.label_login.setText(QtGui.QApplication.translate("UserDialog", "Login:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_password.setText(QtGui.QApplication.translate("UserDialog", "Password:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_group.setText(QtGui.QApplication.translate("UserDialog", "Group:", None, QtGui.QApplication.UnicodeUTF8))
        self.comboBox_group.setItemText(0, QtGui.QApplication.translate("UserDialog", "USER", None, QtGui.QApplication.UnicodeUTF8))
        self.comboBox_group.setItemText(1, QtGui.QApplication.translate("UserDialog", "ADMIN", None, QtGui.QApplication.UnicodeUTF8))

