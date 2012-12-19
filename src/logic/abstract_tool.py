'''
Created on 07.09.2012
@author: vlkv
'''
from PyQt4 import QtCore


class AbstractTool(QtCore.QObject):
    
    def __init__(self):
        super(AbstractTool, self).__init__()
    
    def id(self):
        raise NotImplementedError()
    
    def title(self):
        return "Untitled Tool"
    
    def relatedToolIds(self):
        return []
    
    def connectRelatedTool(self, relatedTool):
        pass
    
    def setRepo(self, repo):
        pass

    def setUser(self, user):
        pass
    
    def storeCurrentState(self):
        pass
    
    def restoreRecentState(self):
        pass
    
    def connectActionsWithActionHandlers(self):
        pass

    def createGui(self, guiParent):
        pass
    
    gui = property(fget=None, fset=None)


    def buildGuiMainMenu(self):
        self.gui.buildActions()
        self.gui.buildMainMenu()
        self.connectActionsWithActionHandlers()
        return self.gui.mainMenu
    
    def enable(self):
        pass
    
    def disable(self):
        pass
    
    def toggleEnableDisable(self, enable):
        if enable:
            self.enable()
        else:
            self.disable()
            
            
    def handlerSignals(self):
        return []
    
    