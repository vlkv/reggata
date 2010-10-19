# -*- coding: utf-8 -*-
'''
Created on 17.10.2010

@author: vlkv
'''

import PyQt4.QtGui as QtGui
import PyQt4.QtCore as QtCore
from db_model import User
import ui_userdialog
from helpers import showExcInfo, tr, DialogMode
from exceptions import UnsupportedDialogModeError
import hashlib

class UserDialog(QtGui.QDialog):
    
    def __init__(self, user, parent=None, mode=DialogMode.CREATE):
        super(UserDialog, self).__init__(parent)
        if type(user) != User:
            raise TypeError(tr("Параметр user должен быть экземпляром User."))
        self.user = user
        self.ui = ui_userdialog.Ui_UserDialog()
        self.ui.setupUi(self)
        self.connect(self.ui.buttonBox, QtCore.SIGNAL("accepted()"), self.button_ok)        
        self.connect(self.ui.buttonBox, QtCore.SIGNAL("rejected()"), self.button_cancel)
        
        self.setMode(mode)
        

    
    def setMode(self, mode):
        if mode == DialogMode.CREATE:
            #TODO
            pass
        elif mode == DialogMode.LOGIN:
            self.ui.label_group.setVisible(False)
            self.ui.comboBox_group.setVisible(False)                        
        else:
            raise UnsupportedDialogModeError(tr("Режим") + mode + tr("не поддерживается."))
        
    
    def write(self):
        '''Запись введенной в элементы gui информации в поля объекта.'''
        self.user.login = self.ui.lineEdit_login.text()
        #TODO Нужно сохранять ХЕШ пароля!!!
        bytes = self.ui.lineEdit_password.text().encode("utf-8")
        self.user.password = hashlib.sha1(bytes).hexdigest()
                
        self.user.group = self.ui.comboBox_group.currentText()
        print(self.user.group)
        
    def button_ok(self):
        try:
            self.write()
            self.user.check_valid()
            self.accept()
        except Exception as ex:
            showExcInfo(self, ex)

    def button_cancel(self):
        self.reject()
        
        