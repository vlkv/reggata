# -*- coding: utf-8 -*-
'''
Created on 21.01.2012
@author: vlkv
'''
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt
from logic.abstract_tool import AbstractTool
from logic.handler_signals import HandlerSignals
from logic.tag_cloud import TagCloud
from logic.action_handlers import *
from gui.common_widgets import Completer
from gui.items_table_tool_gui import ItemsTableToolGui, ItemsTableModel
from parsers import query_parser


class ItemsTable(AbstractTool):
    
    TOOL_ID = "ItemsTableTool"
    
    def __init__(self, widgetsUpdateManager, itemsLock, mainWindow, dialogsFacade):
        super(ItemsTable, self).__init__()
        
        self._repo = None
        self._user = None
        self._gui = None
        self._actionHandlers = None
        
        self._widgetsUpdateManager = widgetsUpdateManager
        self._itemsLock = itemsLock
        self._mainWindow = mainWindow
        self._dialogsFacade = dialogsFacade
        
        self._extAppMgr = ExtAppMgr()
        
        
    def id(self):
        return ItemsTable.TOOL_ID

        
    def title(self):
        return self.tr("Items Table Tool")

        
    def createGui(self, guiParent):
        self._gui = ItemsTableToolGui(guiParent)
        self._actionHandlers = ActionHandlerStorage(self._widgetsUpdateManager)
         
        return self._gui
    
    
    def __getGui(self):
        return self._gui
    gui = property(fget=__getGui)
    
    
    def _getItemsLock(self):
        return self._itemsLock
    itemsLock = property(fget=_getItemsLock)
    
    
    def connectActionsWithActionHandlers(self):
        assert len(self._gui.actions) > 0, "Actions should be already built in ToolGui"
        
        self._actionHandlers.register(
            self._gui.actions['addOneItem'], 
            AddSingleItemActionHandler(self, self._dialogsFacade))
        
        self._actionHandlers.register(
            self._gui.actions['addManyItems'], 
            AddManyItemsActionHandler(self, self._dialogsFacade))
        
        self._actionHandlers.register(
            self._gui.actions['addManuItemsRec'], 
            AddManyItemsRecursivelyActionHandler(self, self._dialogsFacade))
        
        self._actionHandlers.register(
            self._gui.actions['editItem'], 
            EditItemActionHandler(self, self._dialogsFacade))
        
        self._actionHandlers.register(
            self._gui.actions['rebuildItemsThumbnail'], 
            RebuildItemThumbnailActionHandler(self))
        
        self._actionHandlers.register(
            self._gui.actions['deleteItem'], 
            DeleteItemActionHandler(self, self._dialogsFacade))
        
        self._actionHandlers.register(
            self._gui.actions['openItem'], 
            OpenItemActionHandler(self, self._extAppMgr))
        
        
#        self.actions['openItemWithBuiltinImageViewer']
#        self.actions['createM3uAndOpenIt']
#        self.actions['openItemWithExternalFileManager']
#        
#        self.actions['exportItems']
#        self.actions['exportItemsFiles']
#        self.actions['exportItemsFilePaths']
        
    
#        # Separator
#        self.__actionHandlers.registerActionHandler(
#            self.ui.action_item_check_integrity, CheckItemIntegrityActionHandler(self))
#        
#        strategy = {Item.ERROR_FILE_HASH_MISMATCH: FileHashMismatchFixer.TRY_FIND_FILE}
#        self.__actionHandlers.registerActionHandler(
#            self.ui.action_item_fix_hash_error, FixItemIntegrityErrorActionHandler(self, strategy))
#        
#        strategy = {Item.ERROR_FILE_HASH_MISMATCH: FileHashMismatchFixer.UPDATE_HASH}
#        self.__actionHandlers.registerActionHandler(
#            self.ui.action_item_update_file_hash, FixItemIntegrityErrorActionHandler(self, strategy))
#        
#        strategy = {Item.ERROR_HISTORY_REC_NOT_FOUND: HistoryRecNotFoundFixer.TRY_PROCEED_ELSE_RENEW}
#        self.__actionHandlers.registerActionHandler(
#            self.ui.action_item_fix_history_rec_error, FixItemIntegrityErrorActionHandler(self, strategy))
#        
#        strategy = {Item.ERROR_FILE_NOT_FOUND: FileNotFoundFixer.TRY_FIND}
#        self.__actionHandlers.registerActionHandler(
#            self.ui.action_fix_file_not_found_try_find, FixItemIntegrityErrorActionHandler(self, strategy))
#        
#        strategy = {Item.ERROR_FILE_NOT_FOUND: FileNotFoundFixer.DELETE}
#        self.__actionHandlers.registerActionHandler(
#            self.ui.action_fix_file_not_found_delete, FixItemIntegrityErrorActionHandler(self, strategy))

    
    def handlerSignals(self):
        return [([HandlerSignals.ITEM_CHANGED, 
                  HandlerSignals.ITEM_CREATED, 
                  HandlerSignals.ITEM_DELETED], self._gui.update),
                 
                ([HandlerSignals.RESET_SINGLE_ROW], self._gui.resetSingleRow)]
        
    @property
    def repo(self):
        return self._repo
        
        
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
    
    
    def checkActiveRepoIsNotNone(self):
        if self._repo is None:
            raise CurrentRepoIsNoneError("Current repository is None")
    
    
    @property
    def user(self):
        return self._user
    
    def setUser(self, user):
        self._user = user
        userLogin = user.login if user is not None else None
        if self._gui.itemsTableModel is not None:
            self._gui.itemsTableModel.user_login = userLogin 
            
            
    def checkActiveUserIsNotNone(self):
        if self._user is None:
            raise CurrentUserIsNoneError("Current user is None")
    
    
    def restoreRecentState(self):
        self._gui.restore_columns_width()


    def relatedToolIds(self):
        return [TagCloud.TOOL_ID]
    
    
    def connectRelatedTool(self, relatedTool):
        assert relatedTool is not None
        
        if relatedTool.id() == TagCloud.TOOL_ID:
            self.__connectTagCloudTool(relatedTool)
        else:
            assert False, "Unexpected relatedTool.id() = " + str(relatedTool.id())
    
    
    def __connectTagCloudTool(self, tagCloud):
        tagCloud._connectItemsTableTool(self)
        
        
    
