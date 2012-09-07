'''
Created on 20.08.2012
@author: vlkv
'''
import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui
from PyQt4.QtCore import Qt
import os
from logic.abstract_gui import AbstractGui

class GuiProxy(QtGui.QWidget, AbstractGui):
    '''
        This GuiProxy class substitutes MainWindow object in drag'n'drop actions.
    '''
    
    def __init__(self, mainWindow, selectedFiles=[]):
        super(GuiProxy, self).__init__(None)
        self.__mainWindow = mainWindow
        self.__selectedFiles = selectedFiles
        
    def setSelectedFiles(self, selectedFiles):
        self.__selectedFiles = selectedFiles
        
    
    def showMessageOnStatusBar(self, text, timeoutBeforeClear=None):
        self.__mainWindow.showMessageOnStatusBar(text, timeoutBeforeClear)
    
    def checkActiveRepoIsNotNone(self):
        self.__mainWindow.checkActiveRepoIsNotNone()
            
    def checkActiveUserIsNotNone(self):
        self.__mainWindow.checkActiveUserIsNotNone()

    
    def _get_model(self):
        return self.__mainWindow.model
    
    model = property(fget=_get_model)
    
    
        