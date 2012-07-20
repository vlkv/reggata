'''
Created on 20.07.2012

@author: vlkv
'''

import PyQt4.QtGui as QtGui
import PyQt4.QtCore as QtCore
import ui_changeuserpassword
from db_schema import *
from helpers import *
from exceptions import *
from repo_mgr import *


class ChangeUserPasswordDialog(QtGui.QDialog):

    def __init__(self, parent, user):
        super(ChangeUserPasswordDialog, self).__init__(parent)
                
        self.ui = ui_changeuserpassword.Ui_ChangeUserPasswordDialog()
        self.ui.setupUi(self)
        
        assert user is not None
        self.__user = user
        
        self.connect(self.ui.buttonBox, QtCore.SIGNAL("accepted()"), self.buttonOk)        
        self.connect(self.ui.buttonBox, QtCore.SIGNAL("rejected()"), self.buttonCancel)
        
        self.read()


    def read(self):
        self.ui.lineEdit_user_login.setText(self.__user.login)

    def write(self):
        self.__currentPasswordHash = computePasswordHash(self.ui.lineEdit_current_password.text())
        self.__newPassword1Hash = computePasswordHash(self.ui.lineEdit_new_password1.text())
        self.__newPassword2Hash = computePasswordHash(self.ui.lineEdit_new_password2.text())
        self.newPasswordHash = self.__newPassword1Hash
        
    def checkThatCurrentPasswordIsCorrect(self):
        if self.__user.password != self.__currentPasswordHash:
            raise MsgException("Current password is wrong.")
    
    def checkThatTwoNewPasswordsAreTheSame(self):
        if self.__newPassword1Hash != self.__newPassword2Hash:
            raise MsgException("Entered new passwords do not match.")
         
    def checkThatNewPasswordIsNotEmpty(self):
        newPassword = self.ui.lineEdit_new_password1.text()
        if is_none_or_empty(newPassword.strip()):
            raise MsgException("New password should not be empty.")
         
    def buttonOk(self):
        try:
            self.write()
            self.checkThatCurrentPasswordIsCorrect()
            self.checkThatTwoNewPasswordsAreTheSame()
            self.checkThatNewPasswordIsNotEmpty()
            self.accept()
             
        except Exception as ex:
            show_exc_info(self, ex)
    
    def buttonCancel(self):
        self.reject()
    
