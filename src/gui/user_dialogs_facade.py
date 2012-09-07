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
from PyQt4 import QtCore

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
    
    def execItemDialog(self, item, gui, dialogMode):
        completer = Completer(gui.model.repo, gui)
        dialog = ItemDialog(gui, item, dialogMode, completer=completer)
        return dialog.exec_()
    
    
    def execItemsDialog(self, items, gui, dialogMode, sameDstPath):
        completer = Completer(gui.model.repo, gui)
        repoBasePath = gui.model.repo.base_path
        d = ItemsDialog(gui, repoBasePath, items, dialogMode, 
                        same_dst_path=sameDstPath, completer=completer)
        return d.exec_()
     
     
    def startThreadWithWaitDialog(self, thread, gui, indeterminate):
        wd = WaitDialog(gui, indeterminate)
        wd.connect(thread, QtCore.SIGNAL("finished"), wd.reject)
        wd.connect(thread, QtCore.SIGNAL("exception"), wd.exception)
        wd.connect(thread, QtCore.SIGNAL("progress"), wd.set_progress)
        wd.startWithWorkerThread(thread)
        
        
        