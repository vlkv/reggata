'''
Created on 27.08.2012
@author: vvolkov
'''
from gui.user_dialog import UserDialog
from gui.change_user_password_dialog import ChangeUserPasswordDialog
from gui.common_widgets import Completer, WaitDialog
from gui.item_dialog import ItemDialog
from gui.items_dialog import ItemsDialog
from logic.abstract_dialogs_facade import AbstractDialogsFacade
from PyQt4 import QtCore, QtGui
from helpers import is_none_or_empty
import helpers

class UserDialogsFacade(AbstractDialogsFacade):
    '''
        It's a facade-like class, that have functions to invoke different dialogs to
    interact with user. 
    '''

    def execUserDialog(self, user, gui, dialogMode):
        u = UserDialog(user, gui, dialogMode)
        return u.exec_()

    def execChangeUserPasswordDialog(self, user, gui):
        dialog = ChangeUserPasswordDialog(gui, user)
        if dialog.exec_():
            return (True, dialog.newPasswordHash)
        else:
            return (False, None)
    
    def execItemDialog(self, item, gui, repo, dialogMode):
        completer = Completer(repo, gui)
        dialog = ItemDialog(gui, item, repo.base_path, dialogMode, completer=completer)
        return dialog.exec_()
    
    
    def execItemsDialog(self, items, gui, repo, dialogMode, sameDstPath):
        completer = Completer(repo, gui)
        d = ItemsDialog(gui, repo.base_path, items, dialogMode, 
                        same_dst_path=sameDstPath, completer=completer)
        return d.exec_()
     
     
    def startThreadWithWaitDialog(self, thread, gui, indeterminate):
        wd = WaitDialog(gui, indeterminate)
        wd.connect(thread, QtCore.SIGNAL("finished"), wd.reject)
        wd.connect(thread, QtCore.SIGNAL("exception"), wd.exception)
        wd.connect(thread, QtCore.SIGNAL("progress"), wd.set_progress)
        wd.startWithWorkerThread(thread)
        
    
    def getOpenFileName(self, gui, textMessageForUser):
        file = QtGui.QFileDialog.getOpenFileName(gui, textMessageForUser)
        return file
    
    def getOpenFileNames(self, gui, textMessageForUser):
        files = QtGui.QFileDialog.getOpenFileNames(gui, textMessageForUser)
        return files
    
    def getExistingDirectory(self, gui, textMessageForUser):
        dirPath = QtGui.QFileDialog.getExistingDirectory(gui, textMessageForUser)
        return dirPath
    
    def getSaveFileName(self, gui, textMessageForUser):
        filename = QtGui.QFileDialog.getSaveFileName(parent=gui, caption=textMessageForUser)
        return filename
    
    def execMessageBox(self, parent, text, title="Reggata", buttons=[QtGui.QMessageBox.Ok], detailedText=None):
        '''
            Shows modal QtGui.QMessageBox and returns code of the clicked button.
        '''
        mb = QtGui.QMessageBox(parent)
        mb.setText(text)
        mb.setWindowTitle(title)
        
        buttonsCode = QtGui.QMessageBox.NoButton
        for button in buttons:
            buttonsCode = buttonsCode | button
        mb.setStandardButtons(buttonsCode)
        
        if not helpers.is_none_or_empty(detailedText):
            mb.setDetailedText(detailedText)
        
        return mb.exec_()
    
    