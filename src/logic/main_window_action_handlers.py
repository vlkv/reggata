'''
Created on 01.10.2012
@author: vlkv
'''
import os
import PyQt4.QtGui as QtGui
import helpers
import consts
from helpers import show_exc_info
from consts import STATUSBAR_TIMEOUT
from errors import MsgException, LoginError
import ui_aboutdialog
from data.db_schema import User
from data.commands import SaveNewUserCommand, ChangeUserPasswordCommand
from data.repo_mgr import RepoMgr
from logic.ext_app_mgr import ExtAppMgr
from logic.handler_signals import HandlerSignals
from logic.worker_threads import ImportItemsThread
from logic.action_handlers import AbstractActionHandler
from gui.external_apps_dialog import ExternalAppsDialog
from gui.user_dialogs_facade import UserDialogsFacade
from gui.user_dialog import UserDialog

    
class CreateUserActionHandler(AbstractActionHandler):
    def __init__(self, model):
        super(CreateUserActionHandler, self).__init__(model)
        
    def handle(self):
        try:
            self._model.checkActiveRepoIsNotNone()
            
            user = User()
            
            dialogs = UserDialogsFacade()
            if not dialogs.execUserDialog(
                user=user, gui=self._model.gui, dialogMode=UserDialog.CREATE_MODE):
                return
            
            uow = self._model.repo.createUnitOfWork()
            try:
                uow.executeCommand(SaveNewUserCommand(user))
                self._model.user = user
            finally:
                uow.close()
                
        except Exception as ex:
            show_exc_info(self._model.gui, ex)


class LoginUserActionHandler(AbstractActionHandler):
    def __init__(self, model):
        super(LoginUserActionHandler, self).__init__(model)
        
    def handle(self):
        try:
            self._model.checkActiveRepoIsNotNone()
            
            user = User()
            
            dialogs = UserDialogsFacade()
            if not dialogs.execUserDialog(
                user=user, gui=self._model.gui, dialogMode=UserDialog.LOGIN_MODE):
                return
            
            self._model.loginUser(user.login, user.password)
                
        except Exception as ex:
            show_exc_info(self._model.gui, ex)
            
            
class LogoutUserActionHandler(AbstractActionHandler):
    def __init__(self, model):
        super(LogoutUserActionHandler, self).__init__(model)
        
    def handle(self):
        try:
            self._model.user = None
        except Exception as ex:
            show_exc_info(self._model.gui, ex)


class ChangeUserPasswordActionHandler(AbstractActionHandler):
    def __init__(self, model):
        super(ChangeUserPasswordActionHandler, self).__init__(model)
        
    def handle(self):
        try:
            self._model.checkActiveRepoIsNotNone()
            self._model.checkActiveUserIsNotNone()
            
            user = self._model.user
            
            dialogs = UserDialogsFacade()
            dialogExecOk, newPasswordHash = \
                dialogs.execChangeUserPasswordDialog(user=user, gui=self._model.gui)
            if not dialogExecOk:
                return
            
            uow = self._model.repo.createUnitOfWork()
            try:
                command = ChangeUserPasswordCommand(user.login, newPasswordHash)
                uow.executeCommand(command)
            finally:
                uow.close()
                
            user.password = newPasswordHash
            
        except Exception as ex:
            show_exc_info(self._model.gui, ex)
        else:
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Operation completed."), STATUSBAR_TIMEOUT)
    
    
class CreateRepoActionHandler(AbstractActionHandler):
    def  __init__(self, model):
        super(CreateRepoActionHandler, self).__init__(model)
        
    def handle(self):
        try:
            dialogs = UserDialogsFacade()
            basePath = dialogs.getExistingDirectory(
                self._model.gui, self.tr("Choose a base path for new repository"))
            
            if not basePath:
                raise MsgException(
                    self.tr("You haven't chosen existent directory. Operation canceled."))
            
            # QFileDialog returns forward slashes in windows! Because of this 
            # the path should be normalized
            basePath = os.path.normpath(basePath)
            self._model.repo = RepoMgr.createNewRepo(basePath)
            self._model.user = self.__createDefaultUser()
        
        except Exception as ex:
            show_exc_info(self._model.gui, ex)
        
        
    def __createDefaultUser(self):
        self._model.checkActiveRepoIsNotNone()
        
        defaultLogin = consts.DEFAULT_USER_LOGIN
        defaultPassword = helpers.computePasswordHash(consts.DEFAULT_USER_PASSWORD)
        user = User(login=defaultLogin, password=defaultPassword)
        
        uow = self._model.repo.createUnitOfWork()
        try:
            uow.executeCommand(SaveNewUserCommand(user))
        finally:
            uow.close()
        return user


class CloseRepoActionHandler(AbstractActionHandler):
    def __init__(self, model):
        super(CloseRepoActionHandler, self).__init__(model)
        
    def handle(self):
        try:
            self._model.checkActiveRepoIsNotNone()
            self._model.repo = None
            self._model.user = None
            
        except Exception as ex:
            show_exc_info(self._model.gui, ex)
                   
                   
class OpenRepoActionHandler(AbstractActionHandler):
    def __init__(self, model):
        super(OpenRepoActionHandler, self).__init__(model)
        
    def handle(self):
        try:
            dialogs = UserDialogsFacade()
            basePath = dialogs.getExistingDirectory(
                self._model.gui, self.tr("Choose a repository base path"))
            
            if not basePath:
                raise Exception(
                    self.tr("You haven't chosen existent directory. Operation canceled."))

            #QFileDialog returns forward slashes in windows! Because of this path should be normalized
            basePath = os.path.normpath(basePath)
            self._model.repo = RepoMgr(basePath)
            self._model.user = None
            self._model.loginRecentUser()
            
        except LoginError:
            self.__letUserLoginByHimself()
                            
        except Exception as ex:
            show_exc_info(self._model.gui, ex)


    def __letUserLoginByHimself(self):
        user = User()
        dialogs = UserDialogsFacade()
        if not dialogs.execUserDialog(
            user=user, gui=self._model.gui, dialogMode=UserDialog.LOGIN_MODE):
            return
        try:
            self._model.loginUser(user.login, user.password)
        except Exception as ex:
            show_exc_info(self._model.gui, ex)
        
        
class AddCurrentRepoToFavoritesActionHandler(AbstractActionHandler):
    
    def __init__(self, model, favoriteReposStorage):
        super(AddCurrentRepoToFavoritesActionHandler, self).__init__(model)
        self.__favoriteReposStorage = favoriteReposStorage
        
    def handle(self):
        try:
            self._model.checkActiveRepoIsNotNone()
            self._model.checkActiveUserIsNotNone()
            
            repoBasePath = self._model.repo.base_path
            userLogin = self._model.user.login
            
            #TODO: Maybe ask user for a repoAlias...
            self.__favoriteReposStorage.addRepoToFavorites(userLogin, 
                                                           repoBasePath, 
                                                           os.path.basename(repoBasePath))
            
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Current repository saved in favorites list."), STATUSBAR_TIMEOUT)
            self._emitHandlerSignal(HandlerSignals.LIST_OF_FAVORITE_REPOS_CHANGED)
            
        except Exception as ex:
            show_exc_info(self._model.gui, ex)


class RemoveCurrentRepoFromFavoritesActionHandler(AbstractActionHandler):
    def __init__(self, model, favoriteReposStorage):
        super(RemoveCurrentRepoFromFavoritesActionHandler, self).__init__(model)
        self.__favoriteReposStorage = favoriteReposStorage
        
    def handle(self):
        try:
            self._model.checkActiveRepoIsNotNone()
            self._model.checkActiveUserIsNotNone()
            
            repoBasePath = self._model.repo.base_path
            userLogin = self._model.user.login
            
            self.__favoriteReposStorage.removeRepoFromFavorites(userLogin, repoBasePath)
            
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Current repository removed from favorites list."), STATUSBAR_TIMEOUT)
            self._emitHandlerSignal(HandlerSignals.LIST_OF_FAVORITE_REPOS_CHANGED)
            
        except Exception as ex:
            show_exc_info(self._model.gui, ex)


class ImportItemsActionHandler(AbstractActionHandler):
    '''
        Imports previously exported items.
    '''
    def __init__(self, model, dialogs):
        super(ImportItemsActionHandler, self).__init__(model)
        self._dialogs = dialogs
    
    def handle(self):
        try:
            self._model.checkActiveRepoIsNotNone()
            self._model.checkActiveUserIsNotNone()
            
            importFromFilename = self._dialogs.getOpenFileName(
                self._model.gui, 
                self.tr("Open Reggata Archive File"),
                self.tr("Reggata Archive File (*.raf)"))
            if not importFromFilename:
                raise MsgException(self.tr("You haven't chosen a file. Operation canceled."))
            
            thread = ImportItemsThread(self, self._model.repo, importFromFilename, 
                                       self._model.user.login)
            
            self._dialogs.startThreadWithWaitDialog(thread, self._model.gui, indeterminate=False)
            
            self._emitHandlerSignal(HandlerSignals.ITEM_CREATED)
            
            #TODO: display information about how many items were imported
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Operation completed."), STATUSBAR_TIMEOUT)                        
            
        except Exception as ex:
            show_exc_info(self._model.gui, ex)
            
        

class ExitReggataActionHandler(AbstractActionHandler):
    def __init__(self, gui):
        super(ExitReggataActionHandler, self).__init__(gui)
        
    def handle(self):
        try:
            self._gui.close()
        except Exception as ex:
            show_exc_info(self._gui, ex)


class ManageExternalAppsActionHandler(AbstractActionHandler):
    def __init__(self, model, dialogs):
        super(ManageExternalAppsActionHandler, self).__init__(model)
        self._dialogs = dialogs
        
    def handle(self):
        try:
            extAppMgrState = ExtAppMgr.readCurrentState()
            dialog = ExternalAppsDialog(self._model.gui, extAppMgrState, self._dialogs)
            if dialog.exec_() != QtGui.QDialog.Accepted:
                return
            
            ExtAppMgr.setCurrentState(dialog.extAppMgrState())
            self._emitHandlerSignal(HandlerSignals.REGGATA_CONF_CHANGED)
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Operation completed."), STATUSBAR_TIMEOUT)
            
        except Exception as ex:
            show_exc_info(self._model.gui, ex)
        
        
    
    
class ShowAboutDialogActionHandler(AbstractActionHandler):
    def __init__(self, model):
        super(ShowAboutDialogActionHandler, self).__init__(model)
        
    def handle(self):
        try:
            ad = AboutDialog(self._model.gui)
            ad.exec_()
        except Exception as ex:
            show_exc_info(self._model.gui, ex)
        else:
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Operation completed."), STATUSBAR_TIMEOUT)
    
    
    
class AboutDialog(QtGui.QDialog):
    
    def __init__(self, parent=None):
        super(AboutDialog, self).__init__(parent)
        self.ui = ui_aboutdialog.Ui_AboutDialog()
        self.ui.setupUi(self)
        
        title = '''<h1>Reggata</h1>'''
        text = \
'''
<p>Reggata is a tagging system for local files.
</p>

<p>Copyright 2012 Vitaly Volkov, <font color="blue">vitvlkv@gmail.com</font>
</p>

<p>Home page: <font color="blue">http://github.com/vlkv/reggata</font>
</p>

<p>Reggata is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
</p>

<p>Reggata is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
</p>

<p>You should have received a copy of the GNU General Public License
along with Reggata.  If not, see <font color="blue">http://www.gnu.org/licenses</font>.
</p>
'''
        f = None
        try:
            try:
                f = open(os.path.join(os.path.dirname(__file__), "version.txt", "r"))
            except:
                try:
                    f = open(os.path.join(os.path.dirname(__file__), os.pardir, "version.txt"), "r")
                except:
                    f = open(os.path.join(os.path.abspath(os.curdir), "version.txt"), "r")
            version = f.readline()
            text = "<p>Version: " + version + "</p>" + text
        except Exception as ex:
            text = "<p>Version: " + "<font color='red'>&lt;no information&gt;</font>" + "</p>" + text
        finally:
            if f:
                f.close()
                        
        self.ui.textEdit.setHtml(title + text)


class OpenFavoriteRepoActionHandler(AbstractActionHandler):
    def __init__(self, model):
        super(OpenFavoriteRepoActionHandler, self).__init__(model)
    
    def handle(self):
        try:
            action = self.sender()
            repoBasePath = action.repoBasePath
            
            currentUser = self._model.user
            assert currentUser is not None
            
            self._model.repo = RepoMgr(repoBasePath)
            
            try:
                self._model.loginUser(currentUser.login, currentUser.password)
                self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                    self.tr("Repository opened. Login succeded."), STATUSBAR_TIMEOUT)
                
            except LoginError:
                self._model.user = None
                self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                    self.tr("Repository opened. Login failed."), STATUSBAR_TIMEOUT)
        
        except Exception as ex:
            show_exc_info(self._model.gui, ex)
        
        
    
