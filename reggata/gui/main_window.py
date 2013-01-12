# -*- coding: utf-8 -*-
'''
Created on 20.08.2010
@author: vlkv
'''
import os
import logging
from PyQt4 import QtGui, QtCore
import reggata.consts as consts
import reggata.helpers as helpers
import reggata.errors as errors
import reggata.data.repo_mgr as repo
from reggata.logic.abstract_gui import AbstractGui
from reggata.logic.main_window_model import MainWindowModel
from reggata.logic.items_table import ItemsTable
from reggata.logic.handler_signals import HandlerSignals
from reggata.gui.user_dialogs_facade import UserDialogsFacade
from reggata.ui.ui_mainwindow import Ui_MainWindow
from reggata.user_config import UserConfig

logger = logging.getLogger(consts.ROOT_LOGGER + "." + __name__)


class MainWindow(QtGui.QMainWindow, AbstractGui):
    '''
        Reggata's main window.
    '''
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setCentralWidget(None)

        # TODO: updateManager should be moved to MainWindowModel
        self.__widgetsUpdateManager = WidgetsUpdateManager()

        self.__dialogs = UserDialogsFacade()

        self._model = MainWindowModel(mainWindow=self, repo=None, user=None,
                                      guiUpdater=self.__widgetsUpdateManager)

        self.__favoriteReposDynamicQActions = []

        self._model.connectMenuActionsWithHandlers()
        self.__initFavoriteReposMenu()

        self.__initStatusBar()

        self.__widgetsUpdateManager.subscribe(
            self, self.__rebuildFavoriteReposMenu,
            [HandlerSignals.LIST_OF_FAVORITE_REPOS_CHANGED])

        self.__widgetsUpdateManager.subscribe(
            self, self.showMessageOnStatusBar,
            [HandlerSignals.STATUS_BAR_MESSAGE])

        self.__restoreGuiState()


    def widgetsUpdateManager(self):
        return self.__widgetsUpdateManager

    def dialogsFacade(self):
        return self.__dialogs

    def initDockWidgetForTool(self, aTool):
        logger.debug("initDockWidgetForTool() started for tool = {}".format(aTool.id()))
        toolGui = aTool.createGui(self)
        toolDockWidget = QtGui.QDockWidget(aTool.title(), self)
        toolDockWidget.setObjectName(aTool.id() + "DockWidget")
        toolDockWidget.setWidget(toolGui)
        self.addDockWidget(QtCore.Qt.TopDockWidgetArea, toolDockWidget)

        enableDisableAction = toolDockWidget.toggleViewAction()
        self.connect(enableDisableAction, QtCore.SIGNAL("toggled(bool)"), aTool.toggleEnableDisable)
        self.ui.menuTools.addAction(enableDisableAction)


    def addToolMainMenu(self, toolMainMenu):
        assert toolMainMenu is not None
        self.ui.menubar.insertMenu(self.ui.menuHelp.menuAction(), toolMainMenu)


    def subscribeToolForUpdates(self, aTool):
        for handlerSignals, updateCallable in aTool.handlerSignals():
            self.__widgetsUpdateManager.subscribe(aTool, updateCallable, handlerSignals)



    def __initStatusBar(self):
        self.ui.label_repo = QtGui.QLabel()
        self.ui.label_user = QtGui.QLabel()
        self.ui.statusbar.addPermanentWidget(QtGui.QLabel(self.tr("Repository:")))
        self.ui.statusbar.addPermanentWidget(self.ui.label_repo)
        self.ui.statusbar.addPermanentWidget(QtGui.QLabel(self.tr("User:")))
        self.ui.statusbar.addPermanentWidget(self.ui.label_user)


    def closeEvent(self, event):
        self._model.storeCurrentState()
        self.__storeGuiState()
        logger.info("Reggata Main Window is closing")

    def __storeGuiState(self):
        #Store all dock widgets position and size
        byte_arr = self.saveState()
        UserConfig().store("main_window.state", str(byte_arr.data()))

        UserConfig().storeAll({"main_window.width":self.width(), "main_window.height":self.height()})


    def __restoreGuiState(self):

        self._model.restoreRecentState()

        #TODO: move resoring of recent repo and user to the MainWindowModel
        try:
            #Try to open and login recent repository with recent user login
            tmp = UserConfig()["recent_repo.base_path"]
            self._model.repo = repo.RepoMgr(tmp)
            self._model.loginRecentUser()
        except errors.CannotOpenRepoError:
            self.ui.statusbar.showMessage(self.tr("Cannot open recent repository."), consts.STATUSBAR_TIMEOUT)
            self._model.repo = None
        except errors.LoginError:
            self.ui.statusbar.showMessage(self.tr("Cannot login recent repository."), consts.STATUSBAR_TIMEOUT)
            self._model.user = None
        except Exception:
            self.ui.statusbar.showMessage(self.tr("Cannot open/login recent repository."), consts.STATUSBAR_TIMEOUT)

        #Restoring main window size
        width = int(UserConfig().get("main_window.width", 640))
        height = int(UserConfig().get("main_window.height", 480))
        self.resize(width, height)

        #Restoring all dock widgets position and size
        state = UserConfig().get("main_window.state")
        if state:
            state = eval(state)
            self.restoreState(state)


    def __initFavoriteReposMenu(self):
        assert len(self.__favoriteReposDynamicQActions) == 0

        if self._model.user is None:
            return

        actionToInsertBefore =  self.ui.menuFavoriteRepos.insertSeparator(self.ui.actionAdd_current_repository)

        login = self._model.user.login
        favoriteReposInfo = self._model.favoriteRepos(login)
        for repoBasePath, repoAlias in favoriteReposInfo:
            if helpers.is_none_or_empty(repoBasePath):
                continue
            action = QtGui.QAction(self)
            action.setText(repoAlias)
            action.repoBasePath = repoBasePath
            self._model.connectOpenFavoriteRepoAction(action)
            self.ui.menuFavoriteRepos.insertAction(actionToInsertBefore, action)
            self.__favoriteReposDynamicQActions.append(action)


    def __removeDynamicActionsFromFavoriteReposMenu(self):
        for action in self.__favoriteReposDynamicQActions:
            self._model.disconnectOpenFavoriteRepoAction(action)
            self.ui.menuFavoriteRepos.removeAction(action)
        self.__favoriteReposDynamicQActions = []


    def __rebuildFavoriteReposMenu(self):
        self.__removeDynamicActionsFromFavoriteReposMenu()
        self.__initFavoriteReposMenu()


    def event(self, e):
        return super(MainWindow, self).event(e)


    def __get_model(self):
        return self._model
    model = property(fget=__get_model)


    def onCurrentUserChanged(self):
        user = self._model.user
        if user is None:
            self.ui.label_user.setText("")

        else:
            UserConfig().storeAll({"recent_user.login":user.login, "recent_user.password":user.password})

            self.ui.label_user.setText("<b>" + user.login + "</b>")

        self.__rebuildFavoriteReposMenu()


    def onCurrentRepoChanged(self):
        repo = self._model.repo
        try:
            if repo is not None:
                UserConfig().store("recent_repo.base_path", repo.base_path)

                self.ui.label_repo.setText("<b>" + os.path.basename(repo.base_path) + "</b>")
                self.ui.label_repo.setToolTip(repo.base_path)

                self.ui.statusbar.showMessage(self.tr("Opened repository from {}.")
                                              .format(repo.base_path), consts.STATUSBAR_TIMEOUT)
            else:
                self.ui.label_repo.setText("")
                self.ui.label_repo.setToolTip("")

        except Exception as ex:
            raise errors.CannotOpenRepoError(str(ex), ex)


    def showMessageOnStatusBar(self, text, timeoutBeforeClear=None):
        if timeoutBeforeClear is not None:
            self.ui.statusbar.showMessage(text, timeoutBeforeClear)
        else:
            self.ui.statusbar.showMessage(text)

    #TODO: This functions should be removed from MainWindow to Tools
    def selectedRows(self):
        return self._model.toolById(ItemsTable.TOOL_ID).gui.selectedRows()

    def itemAtRow(self, row):
        return self._model.toolById(ItemsTable.TOOL_ID).gui.itemsTableModel.items[row]

    def rowCount(self):
        return self._model.toolById(ItemsTable.TOOL_ID).gui.itemsTableModel.rowCount()

    def resetSingleRow(self, row):
        return self._model.toolById(ItemsTable.TOOL_ID).gui.itemsTableModel.resetSingleRow(row)

    def selectedItemIds(self):
        #Maybe we should use this fun only, and do not use rows outside the GUI code
        itemIds = []
        for row in self.selectedRows():
            itemIds.append(self.itemAtRow(row).id)
        return itemIds



# TODO: Maybe rename to GuiUpdater?
class WidgetsUpdateManager():
    def __init__(self):
        self.__signalsWidgets = dict()
        for handlerSignal in HandlerSignals.allPossibleSignals():
            self.__signalsWidgets[handlerSignal] = []

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

    def onHandlerSignal(self, handlerSignal, *params):
        widgets = self.__signalsWidgets[handlerSignal]
        for aWidget, aCallable in widgets:
            aCallable(*params)
