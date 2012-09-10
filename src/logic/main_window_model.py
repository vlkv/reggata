'''
Created on 07.09.2012
@author: vlkv
'''
from user_config import UserConfig
from data.commands import LoginUserCommand
from errors import CurrentRepoIsNoneError, CurrentUserIsNoneError
from logic.test_tool import TestTool
from logic.items_table import ItemsTable
from logic.tag_cloud import TagCloud
from PyQt4 import QtCore

class AbstractMainWindowModel(object):
    '''
        This is a declarative base class for MainWindowModel, 
    just to be able to quickly find all it's descendants.
    '''
    pass


class MainWindowModel(AbstractMainWindowModel):
    
    def __init__(self, mainWindow, repo, user):
        self._repo = repo
        self._user = user
        self._mainWindow = mainWindow
        
        self._itemsLock = QtCore.QReadWriteLock()
        
        self._tools = []
        
        for tool in self.__getAvailableTools():
            self.__initTool(tool)
    
    
    def _getItemsLock(self):
        return self._itemsLock
    
    itemsLock = property(fget=_getItemsLock)
    

    def __getAvailableTools(self):
        # TODO: Here we shall return a TagCloud, ItemsTable and a FileBrowser
        # TODO: Discovering of tools should be dynamic, like plugin system
        return [TestTool(), 
                ItemsTable(self._mainWindow.widgetsUpdateManager(), 
                           self._itemsLock,
                           self._mainWindow,
                           self._mainWindow.dialogsFacade()),
                TagCloud()]
    
    
    def __initTool(self, aTool):
        self._tools.append(aTool)
        
        self._mainWindow.initDockWidgetForTool(aTool)
        
        aTool.gui.buildActions()
        aTool.connectActionsWithActionHandlers()
        aTool.gui.buildMainMenu()
        if aTool.gui.mainMenu is not None:
            # NOTE: Tool may have no actions and no menus
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
        
