'''
Created on 07.09.2012
@author: vlkv
'''
from reggata.user_config import UserConfig
from reggata.data.commands import LoginUserCommand
from reggata.errors import CurrentRepoIsNoneError, CurrentUserIsNoneError
from reggata.logic.items_table import ItemsTable
from reggata.logic.tag_cloud import TagCloud
from reggata.logic.file_browser import FileBrowser
from reggata.logic.action_handlers import ActionHandlerStorage
import reggata.logic.main_window_action_handlers as handlers
from reggata.logic.favorite_repos_storage import FavoriteReposStorage

class AbstractMainWindowModel(object):
    '''
        This is a declarative base class for MainWindowModel,
    just to be able to quickly find all it's descendants.
    '''
    pass


class MainWindowModel(AbstractMainWindowModel):

    def __init__(self, mainWindow, repo, user, guiUpdater):
        self._repo = repo
        self._user = user
        self._mainWindow = mainWindow

        self.__actionHandlers = ActionHandlerStorage(guiUpdater)

        self.__favoriteReposStorage = FavoriteReposStorage()

        self._tools = []
        for tool in self.__getAvailableTools():
            self.__initTool(tool)


    def __getGui(self):
        return self._mainWindow
    gui = property(fget=__getGui)


    def __getAvailableTools(self):
        # TODO: Discovering of tools should be dynamic, like plugin system
        return [ItemsTable(self._mainWindow.widgetsUpdateManager(),
                           self._mainWindow,
                           self._mainWindow.dialogsFacade()),
                TagCloud(),
                FileBrowser(self._mainWindow.widgetsUpdateManager(),
                            self._mainWindow.dialogsFacade())]


    def __initTool(self, aTool):
        self._tools.append(aTool)

        self._mainWindow.initDockWidgetForTool(aTool)

        toolMainMenu = aTool.buildGuiMainMenu()
        if toolMainMenu is not None:
            self._mainWindow.addToolMainMenu(aTool.gui.mainMenu)

        self.__findAndConnectRelatedToolsFor(aTool)

        self._mainWindow.subscribeToolForUpdates(aTool)


    def __findAndConnectRelatedToolsFor(self, aTool):
        assert aTool is not None

        for relatedToolId in aTool.relatedToolIds():
            relatedTool = self.toolById(relatedToolId)
            if relatedTool is None:
                continue
            aTool.connectRelatedTool(relatedTool)


    def tools(self):
        return self._tools


    def toolById(self, toolId):
        foundTools = [tool for tool in self._tools if tool.id() == toolId]

        if len(foundTools) == 0:
            return None

        assert len(foundTools) == 1, "Tool id=%s is not unique!" % str(toolId)
        return foundTools[0]


    def __get_repo(self):
        return self._repo

    def __set_repo(self, repo):
        self._repo = repo
        self._mainWindow.onCurrentRepoChanged()
        for tool in self._tools:
            tool.setRepo(repo)

    repo = property(fget=__get_repo, fset=__set_repo)


    def __get_user(self):
        return self._user

    def __set_user(self, user):
        self._user = user
        self._mainWindow.onCurrentUserChanged()
        for tool in self._tools:
            tool.setUser(user)

    user = property(fget=__get_user, fset=__set_user)


    def loginRecentUser(self):
        login = UserConfig().get("recent_user.login")
        password = UserConfig().get("recent_user.password")
        self.loginUser(login, password)


    def loginUser(self, login, password):
        self.checkActiveRepoIsNotNone()

        uow = self._repo.createUnitOfWork()
        try:
            user = uow.executeCommand(LoginUserCommand(login, password))
            self.user = user
        finally:
            uow.close()


    def checkActiveRepoIsNotNone(self):
        if self._repo is None:
            raise CurrentRepoIsNoneError("Current repository is None")


    def checkActiveUserIsNotNone(self):
        if self._user is None:
            raise CurrentUserIsNoneError("Current user is None")


    def storeCurrentState(self):
        for tool in self._tools:
            tool.storeCurrentState()


    def restoreRecentState(self):
        #TODO: here we should restore recent user and recent repo. It is done in MainWindow now...
        for tool in self._tools:
            tool.restoreRecentState()


    def favoriteRepos(self, login):
        return self.__favoriteReposStorage.favoriteRepos(login)


    def connectOpenFavoriteRepoAction(self, action):
        actionHandler = handlers.OpenFavoriteRepoActionHandler(self)
        self.__actionHandlers.register(action, actionHandler)


    def disconnectOpenFavoriteRepoAction(self, action):
        self.__actionHandlers.unregister(action)


    def connectMenuActionsWithHandlers(self):
        ui = self._mainWindow.ui

        def initRepositoryMenu():
            self.__actionHandlers.register(
                ui.action_repo_create, handlers.CreateRepoActionHandler(self))

            self.__actionHandlers.register(
                ui.action_repo_close, handlers.CloseRepoActionHandler(self))

            self.__actionHandlers.register(
                ui.action_repo_open, handlers.OpenRepoActionHandler(self))

            self.__actionHandlers.register(
                ui.actionAdd_current_repository,
                handlers.AddCurrentRepoToFavoritesActionHandler(self, self.__favoriteReposStorage))

            self.__actionHandlers.register(
                ui.actionRemove_current_repository,
                handlers.RemoveCurrentRepoFromFavoritesActionHandler(self, self.__favoriteReposStorage))

            self.__actionHandlers.register(
                ui.actionImportItems, handlers.ImportItemsActionHandler(self, self._mainWindow.dialogsFacade()))

            self.__actionHandlers.register(
                ui.actionManageExtApps, handlers.ManageExternalAppsActionHandler(self, self._mainWindow.dialogsFacade()))

            self.__actionHandlers.register(
                ui.actionExitReggata, handlers.ExitReggataActionHandler(self))

        def initUserMenu():
            self.__actionHandlers.register(
                ui.action_user_create, handlers.CreateUserActionHandler(self))

            self.__actionHandlers.register(
                ui.action_user_login, handlers.LoginUserActionHandler(self))

            self.__actionHandlers.register(
                ui.action_user_logout, handlers.LogoutUserActionHandler(self))

            self.__actionHandlers.register(
                ui.action_user_change_pass, handlers.ChangeUserPasswordActionHandler(self))

        def initHelpMenu():
            self.__actionHandlers.register(
                ui.action_help_about, handlers.ShowAboutDialogActionHandler(self))

        initRepositoryMenu()
        initUserMenu()
        initHelpMenu()
