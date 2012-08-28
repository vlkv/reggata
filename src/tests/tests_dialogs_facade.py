'''
Created on 28.08.2012
@author: vvolkov
'''
from logic.abstract_dialogs_facade import AbstractDialogsFacade
import os

class TestsDialogsFacade(AbstractDialogsFacade):
    
    def execUserDialog(self, user, gui, dialogMode):
        return True

    def execChangeUserPasswordDialog(self, user, gui):
        return True
    
    def execItemDialog(self, item, gui, dialogMode):
        
        if item.data_ref is not None:
            item.data_ref.srcAbsPath = item.data_ref.url 
            item.data_ref.dstRelPath = os.path.basename(item.data_ref.url)
        return True
    
    
    def execItemsDialog(self, items, gui, dialogMode, sameDstPath):
        return True
     
    
    def startThreadWithWaitDialog(self, thread, gui, indeterminate):
        thread.run()