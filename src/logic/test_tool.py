'''
Created on 07.09.2012
@author: vlkv
'''
from logic.abstract_tool import AbstractTool
from gui.test_tool_gui import TestToolGui
from PyQt4 import QtCore, QtGui
from logic.handler_signals import HandlerSignals


class TestTool(AbstractTool):
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
        self._gui = TestToolGui(parent=guiParent)
        return self._gui
    
    def __getGui(self):
        return self._gui
    gui = property(fget=__getGui)

    
    def handlerSignals(self):
        return [HandlerSignals.ITEM_CHANGED, HandlerSignals.ITEM_CREATED, 
             HandlerSignals.ITEM_DELETED]
    
    def update(self):
        self._gui.update()
        
        
    
    
    
    
        