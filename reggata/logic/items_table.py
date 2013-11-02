# -*- coding: utf-8 -*-
'''
Created on 21.01.2012
@author: vlkv
'''
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt
from reggata.data.integrity_fixer import FileHashMismatchFixer, FileNotFoundFixer
import reggata.data.db_schema as db
import reggata.data.commands as cmds
from reggata.logic.abstract_tool import AbstractTool
from reggata.logic.tag_cloud import TagCloud
import reggata.logic.action_handlers as handlers
import reggata.logic.items_table_action_handlers as it_handlers
from reggata.logic.ext_app_mgr import ExtAppMgr
from reggata.gui.common_widgets import Completer
from reggata.gui.items_table_gui import ItemsTableGui, ItemsTableModel
from reggata.gui.drop_files_dialogs_facade import DropFilesDialogsFacade
import reggata.errors as errors
from reggata.logic.handler_signals import HandlerSignals
from reggata.gui.univ_table_model import UnivTableColumn
import reggata.consts as consts
from reggata import helpers
import os
import traceback
from reggata.gui.univ_table_settings import UnivTableSettigsDialog



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
        self._actionHandlers = handlers.ActionHandlerStorage(self._widgetsUpdateManager)

        self.__initDragNDropHandlers()

        return self._gui


    def __getGui(self):
        return self._gui
    gui = property(fget=__getGui)

    def createSettingsGui(self, guiParent):
        res = UnivTableSettigsDialog(self._gui.itemsTableModel, "items_table", guiParent)
        return res

    def _getItemsLock(self):
        return self._itemsLock
    itemsLock = property(fget=_getItemsLock)


    def _getWidgetsUpdateManager(self):
        return self._widgetsUpdateManager
    widgetsUpdateManager = property(fget=_getWidgetsUpdateManager)

    def connectActionsWithActionHandlers(self):
        assert len(self._gui.actions) > 0, "Actions should be already built in ToolGui"

        self._actionHandlers.register(
            self._gui.actions['addItems'],
            it_handlers.AddItemsActionHandler(self, self._dialogsFacade))

        self._actionHandlers.register(
            self._gui.actions['editItem'],
            it_handlers.EditItemsActionHandlerItemsTable(self, self._dialogsFacade))

        self._actionHandlers.register(
            self._gui.actions['rebuildItemsThumbnail'],
            it_handlers.RebuildItemThumbnailActionHandler(self))

        self._actionHandlers.register(
            self._gui.actions['deleteItem'],
            it_handlers.DeleteItemActionHandler(self, self._dialogsFacade))

        self._actionHandlers.register(
            self._gui.actions['openItem'],
            it_handlers.OpenItemActionHandler(self, self._extAppMgr))

        self._actionHandlers.register(
            self._gui.actions['openItemWithBuiltinImageViewer'],
            it_handlers.OpenItemWithInternalImageViewerActionHandler(self))

        self._actionHandlers.register(
            self._gui.actions['createM3uAndOpenIt'],
            it_handlers.ExportItemsToM3uAndOpenItActionHandler(self, self._extAppMgr))

        self._actionHandlers.register(
            self._gui.actions['openItemWithExternalFileManager'],
            it_handlers.OpenItemWithExternalFileManagerActionHandler(self, self._extAppMgr))

        self._actionHandlers.register(
            self._gui.actions['exportItems'],
            it_handlers.ExportItemsActionHandler(self, self._dialogsFacade))

        self._actionHandlers.register(
            self._gui.actions['exportItemsFiles'],
            it_handlers.ExportItemsFilesActionHandler(self, self._dialogsFacade))

        self._actionHandlers.register(
            self._gui.actions['exportItemsFilePaths'],
            it_handlers.ExportItemsFilePathsActionHandler(self, self._dialogsFacade))

        self._actionHandlers.register(
            self._gui.actions['checkItemsIntegrity'],
            it_handlers.CheckItemIntegrityActionHandler(self))

        strategy = {db.Item.ERROR_FILE_NOT_FOUND: FileNotFoundFixer.TRY_FIND}
        self._actionHandlers.register(
            self._gui.actions['fixFileNotFoundTryFind'],
            it_handlers.FixItemIntegrityErrorActionHandler(self, strategy))

        strategy = {db.Item.ERROR_FILE_NOT_FOUND: FileNotFoundFixer.DELETE}
        self._actionHandlers.register(
            self._gui.actions['fixFileNotFoundRemoveDataRef'],
            it_handlers.FixItemIntegrityErrorActionHandler(self, strategy))

        strategy = {db.Item.ERROR_FILE_HASH_MISMATCH: FileHashMismatchFixer.TRY_FIND_FILE}
        self._actionHandlers.register(
            self._gui.actions['fixHashMismatchTryFind'],
            it_handlers.FixItemIntegrityErrorActionHandler(self, strategy))

        strategy = {db.Item.ERROR_FILE_HASH_MISMATCH: FileHashMismatchFixer.UPDATE_HASH}
        self._actionHandlers.register(
            self._gui.actions['fixHashMismatchUpdateHash'],
            it_handlers.FixItemIntegrityErrorActionHandler(self, strategy))

        self._actionHandlers.register(
            self._gui.actions['itemsTableSettings'],
            it_handlers.OpenItemsTableSettingsDialog(self))


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
            self._gui.itemsTableModel = ItemsTableModel(repo, self._itemsLock, self.user.login if self.user is not None else None)
            completer = Completer(repo=repo, parent=self._gui)
            self._gui.set_tag_completer(completer)
            self.restoreRecentState()
        else:
            self.storeCurrentState()
            self._gui.itemsTableModel = None
            self._gui.set_tag_completer(None)


    def checkActiveRepoIsNotNone(self):
        if self._repo is None:
            raise errors.CurrentRepoIsNoneError("Current repository is None")


    @property
    def user(self):
        return self._user

    def setUser(self, user):
        self._user = user
        userLogin = user.login if user is not None else None
        if self._gui.itemsTableModel is not None:
            self._gui.itemsTableModel.userLogin = userLogin


    def checkActiveUserIsNotNone(self):
        if self._user is None:
            raise errors.CurrentUserIsNoneError("Current user is None")


    def storeCurrentState(self):
        self._gui.saveColumnsWidth()
        self._gui.saveColumnsVisibility()


    def restoreRecentState(self):
        self._gui.restoreColumnsVisibility()
        self._gui.restoreColumnsWidth()


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


    def acceptDropOfFilesAndDirs(self, files):
        self.__dropFilesDialogs.setSelectedFiles(files)
        self.__dragNDropActionAddItems.trigger()


    def __initDragNDropHandlers(self):
        self.__dragNDropActionAddItems = QtGui.QAction(self)
        self._actionHandlers.register(
            self.__dragNDropActionAddItems, it_handlers.AddItemsActionHandler(self, self.__dropFilesDialogs))
