# -*- coding: utf-8 -*-
'''
Created on 20.08.2010
@author: vlkv
'''
import ui_mainwindow
from consts import *
from data.repo_mgr import *
from logic.worker_threads import *
from logic.integrity_fixer import *
from helpers import *
from gui.tag_cloud import TagCloud
#from gui.file_browser import FileBrowser, FileBrowserTableModel
from gui.items_table_tool_gui import ItemsTableToolGui
from logic.items_table_model import ItemsTableModel
from logic.action_handlers import *
import logging
import consts
import gui.gui_proxy
from logic.abstract_gui import AbstractGui
from logic.favorite_repos_storage import FavoriteReposStorage
from logic.main_window_model import MainWindowModel
from logic.test_tool import TestToolModel

logger = logging.getLogger(consts.ROOT_LOGGER + "." + __name__)


class MainWindow(QtGui.QMainWindow, AbstractGui):
    '''
        Reggata's main window.
    '''
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.ui = ui_mainwindow.Ui_MainWindow()
        self.ui.setupUi(self)
        self.setCentralWidget(None)
        self.setAcceptDrops(True)
        
        self._model = MainWindowModel(mainWindow=self, repo=None, user=None)
        
        # TODO: itemsLock should be in MainWindowModel, or maybe deeper...
        self.items_lock = QtCore.QReadWriteLock()
        
        self.__dialogs = UserDialogsFacade()
        self.__widgetsUpdateManager = WidgetsUpdateManager()
        self.__actionHandlers = ActionHandlerStorage(self.__widgetsUpdateManager)
        self.__favoriteReposStorage = FavoriteReposStorage()
        
        self.__initMenuActions()
        self.__initFavoriteReposMenu()
        self.__initDragNDropHandlers()
        
        self.__initStatusBar()
        self.__initItemsTable()
        self.__initTagCloud()
        #self.__initFileBrowser()
        
        for tool in self.__getAvailableTools():
            self.__initTool(tool)
        
        self.__widgetsUpdateManager.subscribe(
            self, self.__rebuildFavoriteReposMenu, 
            [HandlerSignals.LIST_OF_FAVORITE_REPOS_CHANGED])
        
        self.__restoreGuiState()
        
        
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()
            
    def dropEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
            
            files = []
            for url in event.mimeData().urls():
                files.append(url.toLocalFile())
                
            if len(files) == 1:
                if os.path.isdir(files[0]):
                    self.__acceptDropOfOneDir(files[0])
                elif os.path.isfile(files[0]):
                    self.__acceptDropOfOneFile(files[0])
            else:
                self.__acceptDropOfManyFiles(files)
        else:
            event.ignore()
    
    def __acceptDropOfOneDir(self, dirPath):
        self.__dragNDropGuiProxy.setSelectedFiles([dirPath])
        self.__dragNDropActionItemAddManyRec.trigger()
    
    def __acceptDropOfOneFile(self, file):
        self.__dragNDropGuiProxy.setSelectedFiles([file])
        self.__dragNDropActionItemAdd.trigger()

    def __acceptDropOfManyFiles(self, files):
        self.__dragNDropGuiProxy.setSelectedFiles(files)
        self.__dragNDropActionItemAddMany.trigger()

    
    def __initStatusBar(self):
        self.ui.label_repo = QtGui.QLabel()
        self.ui.label_user = QtGui.QLabel()
        self.ui.statusbar.addPermanentWidget(QtGui.QLabel(self.tr("Repository:")))
        self.ui.statusbar.addPermanentWidget(self.ui.label_repo)
        self.ui.statusbar.addPermanentWidget(QtGui.QLabel(self.tr("User:")))
        self.ui.statusbar.addPermanentWidget(self.ui.label_user)

        
    def __getAvailableTools(self):
        # TODO: Here we shall return a TagCloud, ItemsTable and a FileBrowser
        # TODO: Discovering of tools should be dynamic, like plugin system
        return [TestToolModel()]
    
    def __initTool(self, aTool):
        self._model.addToolModel(aTool)
        
        toolGui = aTool.createGui(self)
        toolDockWidget = QtGui.QDockWidget(aTool.title(), self)
        toolDockWidget.setObjectName(aTool.id() + "DockWidget")
        toolDockWidget.setWidget(toolGui)
        self.addDockWidget(QtCore.Qt.TopDockWidgetArea, toolDockWidget)
        
        # TODO: There should be some config file with settings where to put 
        # menu actions of the tool
        toolMainMenu = aTool.createMainMenuActions(self.ui.menubar, self)
        self.ui.menubar.addAction(toolMainMenu.menuAction())
        
        self.__widgetsUpdateManager.subscribe(
            aTool, aTool.update, aTool.handlerSignals())

        enableDisableAction = toolDockWidget.toggleViewAction()
        self.connect(enableDisableAction, QtCore.SIGNAL("toggled(bool)"), aTool.toggleEnableDisable)
        self.ui.menuTools.addAction(enableDisableAction)
        
    
    

    def __initItemsTable(self):
        self.ui.dockWidget_items_table = ItemsTableToolGui(self)
        itemsTableDockWidget = QtGui.QDockWidget(self.tr("Items Table"), self)
        itemsTableDockWidget.setObjectName("itemsTableDockWidget")
        itemsTableDockWidget.setWidget(self.ui.dockWidget_items_table)
        self.addDockWidget(QtCore.Qt.TopDockWidgetArea, itemsTableDockWidget)
        
        self.menu = self.__createItemsTableContextMenu()
        self.ui.dockWidget_items_table.addContextMenu(self.menu)
        
        self.__widgetsUpdateManager.subscribe(
            self.ui.dockWidget_items_table, self.ui.dockWidget_items_table.query_exec, 
            [HandlerSignals.ITEM_CHANGED, HandlerSignals.ITEM_CREATED, 
             HandlerSignals.ITEM_DELETED])

        self.ui.menuTools.addAction(itemsTableDockWidget.toggleViewAction())


    def __initTagCloud(self):
        self.ui.tag_cloud = TagCloud(self)
        self.ui.dockWidget_tag_cloud = QtGui.QDockWidget(self.tr("Tag cloud"), self)
        self.ui.dockWidget_tag_cloud.setObjectName("dockWidget_tag_cloud")
        self.ui.dockWidget_tag_cloud.setWidget(self.ui.tag_cloud)
        self.addDockWidget(QtCore.Qt.TopDockWidgetArea, self.ui.dockWidget_tag_cloud)
        
        self.connect(self.ui.tag_cloud, QtCore.SIGNAL("selectedTagsChanged"), 
                     self.ui.dockWidget_items_table.selected_tags_changed)
        self.connect(self.ui.dockWidget_items_table, QtCore.SIGNAL("queryTextResetted"), 
                     self.ui.tag_cloud.reset)
        
        self.__widgetsUpdateManager.subscribe(
            self.ui.tag_cloud, self.ui.tag_cloud.refresh, 
            [HandlerSignals.ITEM_CHANGED, HandlerSignals.ITEM_CREATED, 
             HandlerSignals.ITEM_DELETED])
        
        self.ui.menuTools.addAction(self.ui.dockWidget_tag_cloud.toggleViewAction())

#    def __initFileBrowser(self):
#        self.ui.file_browser = FileBrowser(self)
#        self.ui.dockWidget_file_browser = QtGui.QDockWidget(self.tr("File browser"), self)
#        self.ui.dockWidget_file_browser.setObjectName("dockWidget_file_browser")
#        self.ui.dockWidget_file_browser.setWidget(self.ui.file_browser)
#        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.ui.dockWidget_file_browser)
#        self.tabifyDockWidget(self.ui.dockWidget_file_browser, self.ui.dockWidget_items_table)
#        self.ui.menuTools.addAction(self.ui.dockWidget_file_browser.toggleViewAction())

    def __restoreGuiState(self):
        #Try to open and login recent repository with recent user login
        try:
            tmp = UserConfig()["recent_repo.base_path"]
            self._model.repo = RepoMgr(tmp)
            self._model.loginRecentUser()
        except CannotOpenRepoError:
            self.ui.statusbar.showMessage(self.tr("Cannot open recent repository."), STATUSBAR_TIMEOUT)
            self._model.repo = None
        except LoginError:
            self.ui.statusbar.showMessage(self.tr("Cannot login recent repository."), STATUSBAR_TIMEOUT)
            self._model.user = None
        except Exception:
            self.ui.statusbar.showMessage(self.tr("Cannot open/login recent repository."), STATUSBAR_TIMEOUT)
                
        #Restoring columns width of items table
        self.ui.dockWidget_items_table.restore_columns_width()
        
        #Restoring columns width of file browser
        #self.restore_file_browser_state()
        
        #Restoring main window size
        width = int(UserConfig().get("main_window.width", 640))
        height = int(UserConfig().get("main_window.height", 480))
        self.resize(width, height)
        
        #Restoring all dock widgets position and size
        state = UserConfig().get("main_window.state")
        if state:
            state = eval(state)
            self.restoreState(state)


    def __initMenuActions(self):
        def initRepositoryMenu():
            self.__actionHandlers.registerActionHandler(
                self.ui.action_repo_create, CreateRepoActionHandler(self))
            self.__actionHandlers.registerActionHandler(
                self.ui.action_repo_close, CloseRepoActionHandler(self))
            self.__actionHandlers.registerActionHandler(
                self.ui.action_repo_open, OpenRepoActionHandler(self))
            self.__actionHandlers.registerActionHandler(
                self.ui.actionAdd_current_repository, 
                AddCurrentRepoToFavoritesActionHandler(self, self.__favoriteReposStorage))
            self.__actionHandlers.registerActionHandler(
                self.ui.actionRemove_current_repository, 
                RemoveCurrentRepoFromFavoritesActionHandler(self, self.__favoriteReposStorage))
        
        def initUserMenu():
            self.__actionHandlers.registerActionHandler(
                self.ui.action_user_create, CreateUserActionHandler(self))
            self.__actionHandlers.registerActionHandler(
                self.ui.action_user_login, LoginUserActionHandler(self))
            self.__actionHandlers.registerActionHandler(
                self.ui.action_user_logout, LogoutUserActionHandler(self))
            self.__actionHandlers.registerActionHandler(
                self.ui.action_user_change_pass, ChangeUserPasswordActionHandler(self))
            
        def initItemMenu():
            self.__actionHandlers.registerActionHandler(
                self.ui.action_item_add, AddSingleItemActionHandler(self, self.__dialogs))
            self.__actionHandlers.registerActionHandler(
                self.ui.action_item_add_many, AddManyItemsActionHandler(self))
            self.__actionHandlers.registerActionHandler(
                self.ui.action_item_add_many_rec, AddManyItemsRecursivelyActionHandler(self))
            # Separator
            self.__actionHandlers.registerActionHandler(
                self.ui.action_item_edit, EditItemActionHandler(self))
            self.__actionHandlers.registerActionHandler(
                self.ui.action_item_rebuild_thumbnail, RebuildItemThumbnailActionHandler(self))
            # Separator
            self.__actionHandlers.registerActionHandler(
                self.ui.action_item_delete, DeleteItemActionHandler(self))
            # Separator
            self.__actionHandlers.registerActionHandler(
                self.ui.action_item_view, OpenItemActionHandler(self))
            self.__actionHandlers.registerActionHandler(
                self.ui.action_item_view_image_viewer, OpenItemWithInternalImageViewerActionHandler(self))
            self.__actionHandlers.registerActionHandler(
                self.ui.action_item_view_m3u, ExportItemsToM3uAndOpenItActionHandler(self))
            self.__actionHandlers.registerActionHandler(
                self.ui.action_item_to_external_filemanager, OpenItemWithExternalFileManagerActionHandler(self))
            
            self.__actionHandlers.registerActionHandler(
                self.ui.actionExportItems, ExportItemsActionHandler(self))
            self.__actionHandlers.registerActionHandler(
                self.ui.actionImportItems, ImportItemsActionHandler(self))
            self.__actionHandlers.registerActionHandler(
                self.ui.action_export_selected_items, ExportItemsFilesActionHandler(self))
            self.__actionHandlers.registerActionHandler(
                self.ui.action_export_items_file_paths, ExportItemsFilePathsActionHandler(self))
            
            # Separator
            self.__actionHandlers.registerActionHandler(
                self.ui.action_item_check_integrity, CheckItemIntegrityActionHandler(self))
            
            strategy = {Item.ERROR_FILE_HASH_MISMATCH: FileHashMismatchFixer.TRY_FIND_FILE}
            self.__actionHandlers.registerActionHandler(
                self.ui.action_item_fix_hash_error, FixItemIntegrityErrorActionHandler(self, strategy))
            
            strategy = {Item.ERROR_FILE_HASH_MISMATCH: FileHashMismatchFixer.UPDATE_HASH}
            self.__actionHandlers.registerActionHandler(
                self.ui.action_item_update_file_hash, FixItemIntegrityErrorActionHandler(self, strategy))
            
            strategy = {Item.ERROR_HISTORY_REC_NOT_FOUND: HistoryRecNotFoundFixer.TRY_PROCEED_ELSE_RENEW}
            self.__actionHandlers.registerActionHandler(
                self.ui.action_item_fix_history_rec_error, FixItemIntegrityErrorActionHandler(self, strategy))
            
            strategy = {Item.ERROR_FILE_NOT_FOUND: FileNotFoundFixer.TRY_FIND}
            self.__actionHandlers.registerActionHandler(
                self.ui.action_fix_file_not_found_try_find, FixItemIntegrityErrorActionHandler(self, strategy))
            
            strategy = {Item.ERROR_FILE_NOT_FOUND: FileNotFoundFixer.DELETE}
            self.__actionHandlers.registerActionHandler(
                self.ui.action_fix_file_not_found_delete, FixItemIntegrityErrorActionHandler(self, strategy))
            
        def initHelpMenu():
            self.__actionHandlers.registerActionHandler(
                self.ui.action_help_about, ShowAboutDialogActionHandler(self))
            
        initRepositoryMenu()
        initUserMenu()
        initItemMenu()
        initHelpMenu()
        
        
    def __initFavoriteReposMenu(self):
        if self._model.user is None:
            return
        
        actionToInsertBefore =  self.ui.menuFavorite_repositories.insertSeparator(self.ui.actionAdd_current_repository)

        login = self._model.user.login
        favoriteReposInfo = self.__favoriteReposStorage.favoriteRepos(login)
        for repoBasePath, repoAlias in favoriteReposInfo:
            if helpers.is_none_or_empty(repoBasePath):
                continue
            action = QtGui.QAction(self)
            action.setText(repoAlias)
            action.repoBasePath = repoBasePath
            action.handler = OpenFavoriteRepoActionHandler(self)
            self.connect(action, QtCore.SIGNAL("triggered()"), action.handler.handle)
            self.ui.menuFavorite_repositories.insertAction(actionToInsertBefore, action)
        
    
    def __removeDynamicActionsFromFavoriteReposMenu(self):
        preservedActions = [self.ui.actionAdd_current_repository, 
                            self.ui.actionRemove_current_repository]
        self.ui.menuFavorite_repositories.clear()
        for action in preservedActions:
            self.ui.menuFavorite_repositories.addAction(action)
        
    
    def __rebuildFavoriteReposMenu(self):
        self.__removeDynamicActionsFromFavoriteReposMenu()
        self.__initFavoriteReposMenu()
        
            
    
    def __initDragNDropHandlers(self):
        self.__dragNDropGuiProxy = gui.gui_proxy.GuiProxy(self, [])
        
        self.__dragNDropActionItemAdd = QtGui.QAction(self)
        self.__dragNDropActionItemAddMany = QtGui.QAction(self)
        self.__dragNDropActionItemAddManyRec = QtGui.QAction(self)
        
        self.__actionHandlers.registerActionHandler(
            self.__dragNDropActionItemAdd, AddSingleItemActionHandler(self.__dragNDropGuiProxy, self.__dialogs))
        self.__actionHandlers.registerActionHandler(
            self.__dragNDropActionItemAddMany, AddManyItemsActionHandler(self.__dragNDropGuiProxy))
        self.__actionHandlers.registerActionHandler(
            self.__dragNDropActionItemAddManyRec, AddManyItemsRecursivelyActionHandler(self.__dragNDropGuiProxy))


    def __createItemsTableContextMenu(self):
        menu = QtGui.QMenu(self)
        menu.addAction(self.ui.action_item_view)
        menu.addAction(self.ui.action_item_view_m3u)
        menu.addAction(self.ui.action_item_view_image_viewer)
        menu.addAction(self.ui.action_item_to_external_filemanager)
        menu.addMenu(self.ui.menuExport_items)
        menu.addSeparator()
        menu.addAction(self.ui.action_item_edit)
        menu.addAction(self.ui.action_item_rebuild_thumbnail)        
        menu.addSeparator()
        menu.addAction(self.ui.action_item_delete)
        menu.addSeparator()
        menu.addAction(self.ui.action_item_check_integrity)
        menu.addMenu(self.ui.menuFix_integrity_errors)
        return menu
        

    def closeEvent(self, event):
        #Storing all dock widgets position and size
        byte_arr = self.saveState()
        UserConfig().store("main_window.state", str(byte_arr.data()))
        
        #Storing main window size
        UserConfig().storeAll({"main_window.width":self.width(), "main_window.height":self.height()})
        
        self.ui.dockWidget_items_table.save_columns_width()
        
        #Storing file browser table columns width
        #self.save_file_browser_state()
        
        logger.info("Reggata Main Window is closing")
        
        
    
    
#    def restore_file_browser_state(self):
#        self.ui.file_browser.setColumnWidth(FileBrowserTableModel.FILENAME, 
#                                            int(UserConfig().get("file_browser.FILENAME.width", 450)))
#        self.ui.file_browser.setColumnWidth(FileBrowserTableModel.TAGS, 
#                                            int(UserConfig().get("file_browser.TAGS.width", 280)))
#        self.ui.file_browser.setColumnWidth(FileBrowserTableModel.USERS, 
#                                            int(UserConfig().get("file_browser.USERS.width", 100)))
#        self.ui.file_browser.setColumnWidth(FileBrowserTableModel.STATUS, 
#                                            int(UserConfig().get("file_browser.STATUS.width", 100)))
#        self.ui.file_browser.setColumnWidth(FileBrowserTableModel.RATING, 
#                                            int(UserConfig().get("file_browser.RATING.width", 100)))


#    def save_file_browser_state(self):
#        #Storing file browser table columns width
#        width = self.ui.file_browser.columnWidth(FileBrowserTableModel.FILENAME)
#        if width > 0:
#            UserConfig().store("file_browser.FILENAME.width", str(width))
#            
#        width = self.ui.file_browser.columnWidth(FileBrowserTableModel.TAGS)
#        if width > 0:
#            UserConfig().store("file_browser.TAGS.width", str(width))
#        
#        width = self.ui.file_browser.columnWidth(FileBrowserTableModel.USERS)
#        if width > 0:
#            UserConfig().store("file_browser.USERS.width", str(width))
#        
#        width = self.ui.file_browser.columnWidth(FileBrowserTableModel.STATUS)
#        if width > 0:
#            UserConfig().store("file_browser.STATUS.width", str(width))
#                                        
#        width = self.ui.file_browser.columnWidth(FileBrowserTableModel.RATING)
#        if width > 0:
#            UserConfig().store("file_browser.RATING.width", str(width))
                    

    def event(self, e):
        return super(MainWindow, self).event(e)
    
    
    def __get_model(self):
        return self._model
    
    model = property(fget=__get_model)
        
        
    
    def onCurrentUserChanged(self):
        user = self._model.user
        if user is None:
            self.ui.label_user.setText("")
            #self.ui.file_browser.model().user_login = None
            
        else:
            if self.ui.dockWidget_items_table.itemsTableModel is not None:
                self.ui.dockWidget_items_table.itemsTableModel.user_login = user.login
        
            self.ui.label_user.setText("<b>" + user.login + "</b>")
            
            UserConfig().storeAll({"recent_user.login":user.login, "recent_user.password":user.password})
            
            #self.ui.file_browser.model().user_login = user.login
        
        self.__rebuildFavoriteReposMenu()
        


    
    def onCurrentRepoChanged(self):
        repo = self._model.repo
        try:
            self.ui.tag_cloud.repo = repo
            
            if repo is not None:
                UserConfig().store("recent_repo.base_path", repo.base_path)
                
                self.ui.label_repo.setText("<b>" + os.path.basename(repo.base_path) + "</b>")
                self.ui.label_repo.setToolTip(repo.base_path)
                
                self.ui.statusbar.showMessage(self.tr("Opened repository from {}.")
                                              .format(repo.base_path), STATUSBAR_TIMEOUT)
                
                itemsTableModel = ItemsTableModel(
                    repo, self.items_lock, 
                    self._model.user.login if self._model.user is not None else None)
                self.ui.dockWidget_items_table.itemsTableModel = itemsTableModel 
                self.ui.dockWidget_items_table.setTableModel(itemsTableModel)
                #self.ui.file_browser.repo = repo
                 
                #TODO move this completer into the dockWidget_items_table class
                completer = Completer(repo=repo, parent=self.ui.dockWidget_items_table)
                self.ui.dockWidget_items_table.set_tag_completer(completer)
                
                #self.restore_file_browser_state()
                self.ui.dockWidget_items_table.restore_columns_width()
                
            else:
                #self.save_file_browser_state()
                self.ui.dockWidget_items_table.save_columns_width()
                
                self.ui.label_repo.setText("")
                self.ui.label_repo.setToolTip("")
                
                self.ui.dockWidget_items_table.itemsTableModel = None
                self.ui.dockWidget_items_table.setTableModel(None)
                #self.ui.file_browser.repo = None
            
                self.ui.dockWidget_items_table.set_tag_completer(None)
                
        except Exception as ex:
            raise CannotOpenRepoError(str(ex), ex)

        
    def showMessageOnStatusBar(self, text, timeoutBeforeClear=None):
        if timeoutBeforeClear is not None:
            self.ui.statusbar.showMessage(text, timeoutBeforeClear)
        else:
            self.ui.statusbar.showMessage(text)
        
    #TODO: This functions should be moved to ItemsTableWidget and FileBrowserWidget
    def selectedRows(self):
        return self.ui.dockWidget_items_table.selected_rows()
    
    def itemAtRow(self, row):
        return self.ui.dockWidget_items_table.itemsTableModel.items[row]
    
    def rowCount(self):
        return self.ui.dockWidget_items_table.itemsTableModel.rowCount()
    
    def resetSingleRow(self, row):
        self.ui.dockWidget_items_table.itemsTableModel.reset_single_row(row)
            
    def selectedItemIds(self):
        #Maybe we should use this fun only, and do not use rows outside the GUI code
        itemIds = []
        for row in self.selectedRows():
            itemIds.append(self.itemAtRow(row).id)
        return itemIds
    
    def widgetsUpdateManager(self):
        return self.__widgetsUpdateManager
    
            

    
class ActionHandlerStorage():
    def __init__(self, widgetsUpdateManager):
        self.__actions = dict()
        self.__widgetsUpdateManager = widgetsUpdateManager
        
    def registerActionHandler(self, qAction, actionHandler):
        assert not (qAction in self.__actions), "Given qAction already registered"
        
        QtCore.QObject.connect(qAction, QtCore.SIGNAL("triggered()"), actionHandler.handle)
        actionHandler.connectSignals(self.__widgetsUpdateManager)
        
        self.__actions[qAction] = actionHandler
    
    def clear(self):
        for qAction, actionHandler in self.__actions.items():
            actionHandler.disconnectSignals(self.__widgetsUpdateManager)
            QtCore.QObject.disconnect(qAction, QtCore.SIGNAL("triggered()"), actionHandler.handle)
        self.__actions.clear()
    
    
    
class WidgetsUpdateManager():
    def __init__(self):
        self.__signalsWidgets = dict()
        self.__signalsWidgets[HandlerSignals.ITEM_DELETED] = []
        self.__signalsWidgets[HandlerSignals.ITEM_CHANGED] = []
        self.__signalsWidgets[HandlerSignals.ITEM_CREATED] = []
        self.__signalsWidgets[HandlerSignals.LIST_OF_FAVORITE_REPOS_CHANGED] = []
        
    def subscribe(self, widget, widgetUpdateCallable, repoSignals):
        ''' 
            Subscribes 'widget' on 'repoSignals'. Function 'widgetUpdateCallable' 
        will be invoked every time a signal from 'repoSignals' is received.
            'widget' --- some widget that is subscribed to be updated on a number of signals.
            'widgetUpdateCallable' --- function that performs widget update.
            'repoSignals' --- list of signal names on which widget is subscribed.
        '''
        for repoSignal in repoSignals:
            self.__signalsWidgets[repoSignal].append((widget, widgetUpdateCallable))
            
    def unsubscribe(self, widget):
        ''' 
            Unsubscribes given widget from all previously registered signals.
        '''
        for widgets in self.__signalsWidgets.values():
            j = None
            for i in range(len(widgets)):
                aWidget, aCallable = widgets[i]
                if widget == aWidget:
                    j = i
                    break
            if j is not None:
                widgets.pop(j)
    
    def onHandlerSignals(self, handlerSignals):
        alreadyUpdatedWidgets = []
        for handlerSignal in handlerSignals:
            widgets = self.__signalsWidgets[handlerSignal]
            for aWidget, aCallable in widgets:
                if not (aWidget in alreadyUpdatedWidgets):
                    aCallable()
                    alreadyUpdatedWidgets.append(aWidget)
    
    def onHandlerSignal(self, handlerSignal):
        widgets = self.__signalsWidgets[handlerSignal]
        for aWidget, aCallable in widgets:
            aCallable()
            

