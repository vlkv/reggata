# -*- coding: utf-8 -*-
'''
Created on 21.01.2012
@author: vlkv
'''
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt
from data.integrity_fixer import FileHashMismatchFixer, FileNotFoundFixer
from logic.abstract_tool import AbstractTool
from logic.tag_cloud import TagCloud
from logic.action_handlers import *
from logic.items_table_action_handlers import *
from logic.common_action_handlers import *
from logic.ext_app_mgr import ExtAppMgr
from gui.common_widgets import Completer
from gui.items_table_gui import ItemsTableGui, ItemsTableModel
from gui.drop_files_dialogs_facade import DropFilesDialogsFacade


class ItemsTable(AbstractTool):
    
    TOOL_ID = "ItemsTableTool"
    
    def __init__(self, widgetsUpdateManager, mainWindow, dialogsFacade):
        super(ItemsTable, self).__init__()
        
        self._repo = None
        self._user = None
        self._gui = None
        self._actionHandlers = None
        
        #TODO: rename to guiUpdater
        self._widgetsUpdateManager = widgetsUpdateManager
        
        self._itemsLock = QtCore.QReadWriteLock()
        self._mainWindow = mainWindow
        self._dialogsFacade = dialogsFacade
        self.__dropFilesDialogs = DropFilesDialogsFacade(dialogsFacade)
        
        self._extAppMgr = ExtAppMgr()
        
        self._widgetsUpdateManager.subscribe(
            self._extAppMgr, self._extAppMgr.updateState, 
            [HandlerSignals.REGGATA_CONF_CHANGED])
        
        
        
        
    def id(self):
        return ItemsTable.TOOL_ID

        
    def title(self):
        return self.tr("Items Table")

        
    def createGui(self, guiParent):
        self._gui = ItemsTableGui(guiParent, self)
        self._actionHandlers = ActionHandlerStorage(self._widgetsUpdateManager)
        
        self.__initDragNDropHandlers()
         
        return self._gui
    
    
    def __getGui(self):
        return self._gui
    gui = property(fget=__getGui)
    
    
    def _getItemsLock(self):
        return self._itemsLock
    itemsLock = property(fget=_getItemsLock)
    
    
    def _getWidgetsUpdateManager(self):
        return self._widgetsUpdateManager
    widgetsUpdateManager = property(fget=_getWidgetsUpdateManager)
    
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
        
        self._actionHandlers.register(
            self._gui.actions['openItemWithBuiltinImageViewer'],
            OpenItemWithInternalImageViewerActionHandler(self))
        
        self._actionHandlers.register(
            self._gui.actions['createM3uAndOpenIt'],
            ExportItemsToM3uAndOpenItActionHandler(self, self._extAppMgr))
        
        self._actionHandlers.register(
            self._gui.actions['openItemWithExternalFileManager'],
            OpenItemWithExternalFileManagerActionHandler(self, self._extAppMgr))
        
        self._actionHandlers.register(
            self._gui.actions['exportItems'],
            ExportItemsActionHandler(self, self._dialogsFacade))
        
        self._actionHandlers.register(
            self._gui.actions['exportItemsFiles'],
            ExportItemsFilesActionHandler(self, self._dialogsFacade))
        
        self._actionHandlers.register(
            self._gui.actions['exportItemsFilePaths'],
            ExportItemsFilePathsActionHandler(self, self._dialogsFacade))
        
        self._actionHandlers.register(
            self._gui.actions['checkItemsIntegrity'],
            CheckItemIntegrityActionHandler(self))
        
        strategy = {Item.ERROR_FILE_NOT_FOUND: FileNotFoundFixer.TRY_FIND}
        self._actionHandlers.register(
            self._gui.actions['fixFileNotFoundTryFind'],
            FixItemIntegrityErrorActionHandler(self, strategy))
        
        strategy = {Item.ERROR_FILE_NOT_FOUND: FileNotFoundFixer.DELETE}
        self._actionHandlers.register(
            self._gui.actions['fixFileNotFoundRemoveDataRef'],
            FixItemIntegrityErrorActionHandler(self, strategy))
        
        strategy = {Item.ERROR_FILE_HASH_MISMATCH: FileHashMismatchFixer.TRY_FIND_FILE}
        self._actionHandlers.register(
            self._gui.actions['fixHashMismatchTryFind'],
            FixItemIntegrityErrorActionHandler(self, strategy))
        
        strategy = {Item.ERROR_FILE_HASH_MISMATCH: FileHashMismatchFixer.UPDATE_HASH}
        self._actionHandlers.register(
            self._gui.actions['fixHashMismatchUpdateHash'],
            FixItemIntegrityErrorActionHandler(self, strategy))
    
    
    def handlerSignals(self):
        return [([HandlerSignals.ITEM_CHANGED,
                  HandlerSignals.ITEM_CREATED,
                  HandlerSignals.ITEM_DELETED], self._gui.update),
                 
                ([HandlerSignals.RESET_SINGLE_ROW], self._gui.resetSingleRow),
                ([HandlerSignals.RESET_ROW_RANGE], self._gui.resetRowRange)]
        
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
    
    
    def storeCurrentState(self):
        self._gui.save_columns_width()
        
    
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
        
        
    
    
    def acceptDropOfOneDir(self, dirPath):
        self.__dropFilesDialogs.setSelectedFiles([dirPath])
        self.__dragNDropActionItemAddManyRec.trigger()
    
    
    def acceptDropOfOneFile(self, file):
        self.__dropFilesDialogs.setSelectedFiles([file])
        self.__dragNDropActionItemAdd.trigger()


    def acceptDropOfManyFiles(self, files):
        self.__dropFilesDialogs.setSelectedFiles(files)
        self.__dragNDropActionItemAddMany.trigger()

    
    def __initDragNDropHandlers(self):
        
        self.__dragNDropActionItemAdd = QtGui.QAction(self)
        self.__dragNDropActionItemAddMany = QtGui.QAction(self)
        self.__dragNDropActionItemAddManyRec = QtGui.QAction(self)
        
        self._actionHandlers.register(
            self.__dragNDropActionItemAdd, AddSingleItemActionHandler(self, self.__dropFilesDialogs))
        self._actionHandlers.register(
            self.__dragNDropActionItemAddMany, AddManyItemsActionHandler(self, self.__dropFilesDialogs))
        self._actionHandlers.register(
            self.__dragNDropActionItemAddManyRec, AddManyItemsRecursivelyActionHandler(self, self.__dropFilesDialogs))

    
