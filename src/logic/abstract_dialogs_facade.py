'''
Created on 28.08.2012
@author: vvolkov
'''

class AbstractDialogsFacade(object):
 
    def execUserDialog(self, user, gui, dialogMode):
        raise NotImplementedError()

    def execChangeUserPasswordDialog(self, user, gui):
        raise NotImplementedError()
    
    def execItemDialog(self, item, gui, repo, dialogMode):
        raise NotImplementedError()
    
    def execItemsDialog(self, items, gui, repo, dialogMode, sameDstPath):
        raise NotImplementedError()
    
    def startThreadWithWaitDialog(self, thread, gui, indeterminate):
        raise NotImplementedError()
    
    def getOpenFileName(self, gui, textMessageForUser):
        raise NotImplementedError()
    
    def getOpenFileNames(self, gui, textMessageForUser):
        raise NotImplementedError()
    
    def getExistingDirectory(self, gui, textMessageForUser):
        raise NotImplementedError()
    
    def getSaveFileName(self, gui, textMessageForUser):
        raise NotImplementedError()
    