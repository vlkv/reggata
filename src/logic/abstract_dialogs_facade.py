'''
Created on 28.08.2012
@author: vvolkov
'''

class AbstractDialogsFacade(object):
 
    def execUserDialog(self, user, gui, dialogMode):
        raise NotImplementedError()

    def execChangeUserPasswordDialog(self, user, gui):
        raise NotImplementedError()
    
    def execItemDialog(self, item, gui, dialogMode):
        raise NotImplementedError()
    
    def execItemsDialog(self, items, gui, dialogMode, sameDstPath):
        raise NotImplementedError()
    
    def startThreadWithWaitDialog(self, thread, gui, indeterminate):
        raise NotImplementedError()