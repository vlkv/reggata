'''
Created on 07.09.2012
@author: vlkv
'''
from user_config import UserConfig
from data.commands import LoginUserCommand

class MainWindowModel(object):
    
    def __init__(self, mainWindow, repo, user):
        self._repo = repo
        self._user = user
        self._mainWindow = mainWindow
    
    
    def __get_repo(self):
        return self._repo
    
    def __set_repo(self, repo):
        self._repo = repo
        self._mainWindow.onCurrentRepoChanged()
    
    repo = property(fget=__get_repo, fset=__set_repo)
        
        
    def __get_user(self):
        return self._user
    
    def __set_user(self, user):
        self._user = user
        self._mainWindow.onCurrentUserChanged()
    
    user = property(fget=__get_user, fset=__set_user)
    
    
    
    def loginRecentUser(self):
        login = UserConfig().get("recent_user.login")
        password = UserConfig().get("recent_user.password")
        self.loginUser(login, password)
        
        
    def loginUser(self, login, password):
        self._mainWindow.checkActiveRepoIsNotNone()
        
        uow = self._repo.createUnitOfWork()
        try:
            user = uow.executeCommand(LoginUserCommand(login, password))
            self.user = user
        finally:
            uow.close()


