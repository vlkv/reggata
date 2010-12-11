# -*- coding: utf-8 -*-
'''
Copyright 2010 Vitaly Volkov

This file is part of Reggata.

Reggata is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Reggata is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Reggata.  If not, see <http://www.gnu.org/licenses/>.

Created on 17.10.2010

@author: vlkv
'''

import PyQt4.QtGui as QtGui
import PyQt4.QtCore as QtCore
from db_schema import User
import ui_userdialog
from helpers import show_exc_info, tr, DialogMode
from exceptions import UnsupportedDialogModeError, MsgException
import hashlib

class UserDialog(QtGui.QDialog):
    
    def __init__(self, user, parent=None, mode=DialogMode.CREATE):
        super(UserDialog, self).__init__(parent)
        if type(user) != User:
            raise TypeError(self.tr("Argument user must be a User class instance."))
        self.user = user
        self.ui = ui_userdialog.Ui_UserDialog()
        self.ui.setupUi(self)
        self.mode = None
        
        #TODO Пока что поле group не используется, поэтому пока что спрячем
        self.ui.label_group.setVisible(False)
        self.ui.comboBox_group.setVisible(False)
        
        self.connect(self.ui.buttonBox, QtCore.SIGNAL("accepted()"), self.button_ok)        
        self.connect(self.ui.buttonBox, QtCore.SIGNAL("rejected()"), self.button_cancel)
        
        self.setMode(mode)
        
        self.read()

    
    def setMode(self, mode):
        if mode == DialogMode.CREATE:
            pass
            
        elif mode == DialogMode.LOGIN:
            self.ui.label_password_repeat.setVisible(False)
            self.ui.lineEdit_password_repeat.setVisible(False)
            
            self.ui.label_group.setVisible(False)
            self.ui.comboBox_group.setVisible(False)
        else:
            raise UnsupportedDialogModeError(self.tr("DialogMode={} is not supported by this dialog.").format(mode))
        self.mode = mode
    
    def read(self):
        #TODO
        pass    
    
    def write(self):
        '''Запись введенной в элементы gui информации в поля объекта.'''
        self.user.login = self.ui.lineEdit_login.text()
        if self.mode == DialogMode.CREATE and self.ui.lineEdit_password.text() != self.ui.lineEdit_password_repeat.text():
            raise MsgException(self.tr("Entered passwords do not match."))        
        
        bytes = self.ui.lineEdit_password.text().encode("utf-8")
        self.user.password = hashlib.sha1(bytes).hexdigest()
                
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
        
        