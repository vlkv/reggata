'''
Created on 07.09.2012
@author: vlkv
'''

class MainWindowModel(object):
    
    def __init__(self, mainWindow, repo, user):
        self._repo = repo
        self._user = user
        self._mainWindow = mainWindow
    
    
    def __get_repo(self):
        return self._repo
    
    def __set_repo(self, repo):
        self._repo = repo
    
    repo = property(fget=__get_repo, fset=__set_repo)
        
        
    def __get_user(self):
        return self._user
    
    def __set_user(self, user):
        self._user = user
        self._mainWindow.onUserChanged()
    
    user = property(fget=__get_user, fset=__set_user)
    
    
    
        