# -*- coding: utf-8 -*-
'''
Created on 17.10.2010
@author: vlkv
'''
import PyQt4.QtGui as QtGui
import PyQt4.QtCore as QtCore
from data.db_schema import User
from ui.ui_userdialog import Ui_UserDialog
from helpers import show_exc_info, computePasswordHash
from errors import UnsupportedDialogModeError, MsgException


class UserDialog(QtGui.QDialog):
    
    CREATE_MODE = "CREATE_MODE"
    LOGIN_MODE = "LOGIN_MODE"
    
    def __init__(self, user, parent, mode):
        super(UserDialog, self).__init__(parent)
        if type(user) != User:
            raise TypeError(self.tr("Argument user must be a User class instance."))
        self.user = user
        self.ui = Ui_UserDialog()
        self.ui.setupUi(self)
        self.mode = None
        
        self.ui.label_group.setVisible(False)
        self.ui.comboBox_group.setVisible(False)
        
        self.connect(self.ui.buttonBox, QtCore.SIGNAL("accepted()"), self.button_ok)        
        self.connect(self.ui.buttonBox, QtCore.SIGNAL("rejected()"), self.button_cancel)
        
        self.setMode(mode)

    
    def setMode(self, mode):
        if mode == UserDialog.CREATE_MODE:
            self.setWindowTitle(self.tr("Create new repository user"))
            
            self.ui.label_notice.setVisible(False)
            
        elif mode == UserDialog.LOGIN_MODE:
            self.setWindowTitle(self.tr("Repository login"))
            
            self.ui.label_password_repeat.setVisible(False)
            self.ui.lineEdit_password_repeat.setVisible(False)
            
            self.ui.label_group.setVisible(False)
            self.ui.comboBox_group.setVisible(False)
        else:
            raise UnsupportedDialogModeError(self.tr("Mode={} is not supported by this dialog.")
                                             .format(mode))
        
        self.mode = mode
        
        
    def write(self):
        self.user.login = self.ui.lineEdit_login.text()
        if self.mode == UserDialog.CREATE_MODE \
        and self.ui.lineEdit_password.text() != self.ui.lineEdit_password_repeat.text():
            raise MsgException(self.tr("Entered passwords do not match."))
        
        self.user.password = computePasswordHash(self.ui.lineEdit_password.text())
                
        self.user.group = self.ui.comboBox_group.currentText()
        
    def button_ok(self):
        try:
            self.write()
            self.user.check_valid()
            self.accept()
        except Exception as ex:
            show_exc_info(self, ex)

    def button_cancel(self):
        self.reject()
        
        