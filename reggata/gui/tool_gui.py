'''
Created on 09.09.2012
@author: vlkv
'''
import logging
from PyQt4 import QtGui
from reggata.logic.abstract_tool_gui import AbstractToolGui
import reggata.consts as consts

logger = logging.getLogger(consts.ROOT_LOGGER + "." + __name__)


class ToolGui(QtGui.QWidget, AbstractToolGui):
    '''
        This is a base class for all Gui-s of Tools.
    '''

    def __init__(self, parent):
        logging.debug("ToolGui __init__")
        super(ToolGui, self).__init__(parent)

        self._actions = dict()
        self._mainMenu = None
        self._contextMenu = None


    def __getActions(self):
        return self._actions
    actions = property(fget=__getActions)


    def __getMainMenu(self):
        return self._mainMenu
    mainMenu = property(fget=__getMainMenu)


    def buildActions(self):
        pass


    def buildMainMenu(self):
        pass


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
