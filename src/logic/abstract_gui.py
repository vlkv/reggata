'''
Created on 21.08.2012
@author: vlkv
'''

class AbstractGui(object):
    '''
        This interface is used in action_handlers. It is implemented by 
    MainWindow, GuiProxy, TestsGui.
    '''
    
    def setSelectedFiles(self, selectedFiles):
        raise NotImplementedError()
    
    
    def showMessageOnStatusBar(self, text, timeoutBeforeClear=None):
        raise NotImplementedError()
    
    def checkActiveRepoIsNotNone(self):
        raise NotImplementedError()
            
    def checkActiveUserIsNotNone(self):
        raise NotImplementedError()
    

    def _get_model(self):
        raise NotImplementedError()
    
    model = property(fget=_get_model)
    
        
    
    def widgetsUpdateManager(self):
        raise NotImplementedError()
    
    