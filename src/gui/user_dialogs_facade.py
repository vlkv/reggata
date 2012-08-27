'''
Created on 27.08.2012
@author: vvolkov
'''
from gui.user_dialog import UserDialog

class UserDialogsFacade(object):
    '''
        It's a facade-like class, that have functions to invoke different dialogs to
    interact with user. 
    '''

    def execUserDialog(self, user, gui, dialogMode):
        u = UserDialog(user, gui, dialogMode)
        return u.exec_()

    