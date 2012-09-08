'''
Created on 07.09.2012
@author: vlkv
'''
from logic.abstract_tool import AbstractTool
from gui.test_tool_gui import TestToolGui
from PyQt4 import QtCore, QtGui
from logic.handler_signals import HandlerSignals


class TestTool(QtCore.QObject, AbstractTool):
    '''
        This is an minimal Tool that does nothing. It can be used as a template for creating new Tools.
    '''
    def __init__(self):
        super(TestTool, self).__init__()

        
    def id(self):
        return type(self).__name__

        
    def title(self):
        return self.tr("Test Tool")

        
    def createGui(self, guiParent):
        self._gui = TestToolGui(guiParent) 
        return self._gui

    
    def createMainMenuActions(self, menuParent, actionsParent):
        menu = QtGui.QMenu(menuParent)
        menu.setTitle(self.tr("Test Tool Menu"))
        
        action1 = QtGui.QAction(actionsParent)
        action1.setText(self.tr("Action 1"))
        menu.addAction(action1)
        
        action2 = QtGui.QAction(actionsParent)
        action2.setText(self.tr("Action 2"))
        menu.addAction(action2)
        
        return menu

    
    def handlerSignals(self):
        return [HandlerSignals.ITEM_CHANGED, HandlerSignals.ITEM_CREATED, 
             HandlerSignals.ITEM_DELETED]


    def enable(self):
        pass

    
    def disable(self):
        pass

    
    def toggleEnableDisable(self, enable):
        if enable:
            self.enable()
        else:
            self.disable()
    
    
    def update(self):
        self._gui.update()
        
        
    def setRepo(self, repo):
        pass

    def setUser(self, user):
        pass
    
    def restoreRecentState(self):
        pass
    
    
    
        