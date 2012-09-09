'''
Created on 07.09.2012
@author: vlkv
'''
from PyQt4 import QtCore

class AbstractTool(QtCore.QObject):
    
    def __init__(self):
        super(AbstractTool, self).__init__()
    
    def createMainMenuActions(self, menuParent, actionsParent):
        return None
    
    def relatedToolIds(self):
        return []
    
    def connectRelatedTool(self, relatedTool):
        pass
    
    
    
    