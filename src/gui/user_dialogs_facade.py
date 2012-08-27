'''
Created on 27.08.2012
@author: vvolkov
'''
from gui.user_dialog import UserDialog
from gui.change_user_password_dialog import ChangeUserPasswordDialog
from gui.common_widgets import Completer
from gui.item_dialog import ItemDialog
from gui.items_dialog import ItemsDialog

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
    
    def execItemDialog(self, item, gui, dialogMode):
        completer = Completer(gui.active_repo, gui)
        dialog = ItemDialog(gui, item, dialogMode, completer=completer)
        return dialog.exec_()
    
    
    def execItemsDialog(self, items, gui, dialogMode, sameDstPath):
        completer = Completer(gui.active_repo, gui)
        repoBasePath = gui.active_repo.base_path
        d = ItemsDialog(gui, repoBasePath, items, dialogMode, 
                        same_dst_path=sameDstPath, completer=completer)
        return d.exec_()
     
    