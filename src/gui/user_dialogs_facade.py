'''
Created on 27.08.2012
@author: vvolkov
'''
from gui.user_dialog import UserDialog
from gui.change_user_password_dialog import ChangeUserPasswordDialog

class UserDialogsFacade(object):
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
    