# -*- coding: utf-8 -*-
'''
Created on 21.01.2012

@author: vlkv
'''
import os
import consts
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt
import traceback
from data.db_schema import Item, DataRef
from parsers import query_parser
from logic.worker_threads import ThumbnailBuilderThread
from data.repo_mgr import *
from data.commands import *
from logic.abstract_tool import AbstractTool
from gui.items_table_tool_gui import ItemsTableToolGui, ItemsTableModel
from logic.handler_signals import HandlerSignals
from gui.common_widgets import Completer


class ItemsTable(QtCore.QObject, AbstractTool):
    
    TOOL_ID = "ItemsTable"
    
    def __init__(self, itemsLock):
        super(ItemsTable, self).__init__()
        
        self._repo = None
        self._user = None
        
        self._itemsLock = itemsLock
        
        self._gui = None
        
        
    def id(self):
        return ItemsTable.TOOL_ID

        
    def title(self):
        return self.tr("Items Table Tool")

        
    def createGui(self, guiParent):
        self._gui = ItemsTableToolGui(guiParent) 
        return self._gui
    
    def gui(self):
        return self._gui

    
    def createMainMenuActions(self, menuParent, actionsParent):
        menu = QtGui.QMenu(menuParent)
        menu.setTitle(self.tr("Items Table"))
        
        # TODO create and return correct actions
        
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
        self._repo = repo
        if repo is not None:
            itemsTableModel = ItemsTableModel(repo, self._itemsLock,
                                              self._user.login if self._user is not None else None)
            self._gui.itemsTableModel = itemsTableModel 
            
            completer = Completer(repo=repo, parent=self._gui)
            self._gui.set_tag_completer(completer)

            self._gui.restore_columns_width()
        else:
            self._gui.save_columns_width()
            
            self._gui.itemsTableModel = None
        
            self._gui.set_tag_completer(None)
    
    def setUser(self, user):
        self._user = user
        userLogin = user.login if user is not None else None
        if self._gui.itemsTableModel is not None:
            self._gui.itemsTableModel.user_login = userLogin
    
    
    def restoreRecentState(self):
        self._gui.restore_columns_width()


    def baseToolIds(self):
        return []
    
    
