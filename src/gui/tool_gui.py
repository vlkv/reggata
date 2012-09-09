'''
Created on 09.09.2012
@author: vlkv
'''
from PyQt4 import QtGui

class ToolGui(QtGui.QWidget):

    def __init__(self, parent):
        super(ToolGui, self).__init__(parent)
        
        self._actions = dict()
    
    def __getActions(self):
        return self._actions
    actions = property(fget=__getActions)
    

    def _createMenu(self, menuTitle, menuParent):
        menu = QtGui.QMenu(menuParent)
        menu.setTitle(menuTitle)
        return menu
    
    def _createAndAddSubMenu(self, subMenuTitle, subMenuParent, parentMenu):
        subMenu = self._createMenu(subMenuTitle, subMenuParent)
        parentMenu.addMenu(subMenu)
        return subMenu
    
    def _createAction(self, actionTitle):
        action = QtGui.QAction(self)
        action.setText(actionTitle)
        return action
    
    