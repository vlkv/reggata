'''
Created on 21.08.2012
@author: vlkv
'''

class AbstractGui(object):
    '''
    This interface is used in action_handlers. It is implemented by MainWindow and GuiProxy.
    '''
    
    def setSelectedFiles(self, selectedFiles):
        raise NotImplementedError()


    # TODO: Move this group of functions to UserDialogsFacade
    def getOpenFileName(self, textMessageForUser):
        raise NotImplementedError()

    def getOpenFileNames(self, textMessageForUser):
        raise NotImplementedError()
    
    def getExistingDirectory(self, textMessageForUser):
        raise NotImplementedError()
    
    def getSaveFileName(self, textMessageForUser):
        raise NotImplementedError()
    
    
    
    def showMessageOnStatusBar(self, text, timeoutBeforeClear=None):
        raise NotImplementedError()
    
    def checkActiveRepoIsNotNone(self):
        raise NotImplementedError()
            
    def checkActiveUserIsNotNone(self):
        raise NotImplementedError()
    

    def _get_active_repo(self):
        raise NotImplementedError()
    
    def _set_active_repo(self, repo):
        raise NotImplementedError()
        
    active_repo = property(_get_active_repo, 
                           _set_active_repo)
    
    
    def _get_model(self):
        raise NotImplementedError()
    
    model = property(fget=_get_model)
    
        
    
    def widgetsUpdateManager(self):
        raise NotImplementedError()
    
    