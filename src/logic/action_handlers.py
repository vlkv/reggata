# -*- coding: utf-8 -*-
'''
Created on 23.07.2012

@author: vlkv
'''
import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui
from data.repo_mgr import *
from consts import *
from helpers import *
from gui.change_user_password_dialog import ChangeUserPasswordDialog
from gui.item_dialog import ItemDialog
from gui.items_dialog import ItemsDialog
import ui_aboutdialog
from gui.common_widgets import Completer, WaitDialog
from logic.ext_app_mgr import ExtAppMgr
from gui.image_viewer import ImageViewer
from logic.worker_threads import *
from errors import *
from gui.my_message_box import MyMessageBox
from gui.user_dialogs_facade import UserDialogsFacade
from gui.user_dialog import UserDialog
from logic.handler_signals import HandlerSignals


class ActionHandlerStorage():
    def __init__(self, widgetsUpdateManager):
        self.__actions = dict()
        self.__widgetsUpdateManager = widgetsUpdateManager
    
    def register(self, qAction, actionHandler):
        assert not (qAction in self.__actions), "Given qAction already registered"
        
        QtCore.QObject.connect(qAction, QtCore.SIGNAL("triggered()"), actionHandler.handle)
        actionHandler.connectSignals(self.__widgetsUpdateManager)
        
        self.__actions[qAction] = actionHandler
    
    def unregister(self, qAction):
        assert qAction in self.__actions, "qAction must be registered before"
        actionHandler = self.__actions[qAction]
        
        actionHandler.disconnectSignals(self.__widgetsUpdateManager)
        QtCore.QObject.disconnect(qAction, QtCore.SIGNAL("triggered()"), actionHandler.handle)
        
        del self.__actions[qAction]
    
    def unregisterAll(self):
        for qAction, actionHandler in self.__actions.items():
            actionHandler.disconnectSignals(self.__widgetsUpdateManager)
            QtCore.QObject.disconnect(qAction, QtCore.SIGNAL("triggered()"), actionHandler.handle)
        
        self.__actions.clear()



class AbstractActionHandler(QtCore.QObject):
    def __init__(self, model=None):
        super(AbstractActionHandler, self).__init__()
        self._gui = model # TODO: remove self._gui as soon as possible from here
        self._tool = model # TODO: remove self._tool also..
        self._model = model
        
    def handle(self):
        raise NotImplementedError("This function should be overriden in subclass")

    def connectSignals(self, widgetsUpdateManager):
        self.connect(self, QtCore.SIGNAL("handlerSignal"), \
                     widgetsUpdateManager.onHandlerSignal)
        self.connect(self, QtCore.SIGNAL("handlerSignals"), \
                     widgetsUpdateManager.onHandlerSignals)
    
    def disconnectSignals(self, widgetsUpdateManager):
        self.disconnect(self, QtCore.SIGNAL("handlerSignal"), \
                     widgetsUpdateManager.onHandlerSignal)
        self.disconnect(self, QtCore.SIGNAL("handlerSignals"), \
                     widgetsUpdateManager.onHandlerSignals)
        
    def _emitHandlerSignal(self, handlerSignalType, *params):
        self.emit(QtCore.SIGNAL("handlerSignal"), handlerSignalType, *params)
    
    def _emitHandlerSignals(self, handlerSignalTypes):
        self.emit(QtCore.SIGNAL("handlerSignals"), handlerSignalTypes)
    
    
class CreateUserActionHandler(AbstractActionHandler):
    def __init__(self, gui):
        super(CreateUserActionHandler, self).__init__(gui)
        
    def handle(self):
        try:
            self._gui.model.checkActiveRepoIsNotNone()
            
            user = User()
            
            dialogs = UserDialogsFacade()
            if not dialogs.execUserDialog(
                user=user, gui=self._gui, dialogMode=UserDialog.CREATE_MODE):
                return
            
            uow = self._gui.model.repo.createUnitOfWork()
            try:
                uow.executeCommand(SaveNewUserCommand(user))
                self._gui.model.user = user
            finally:
                uow.close()
                
        except Exception as ex:
            show_exc_info(self._gui, ex)

class LoginUserActionHandler(AbstractActionHandler):
    def __init__(self, gui):
        super(LoginUserActionHandler, self).__init__(gui)
        
    def handle(self):
        try:
            self._gui.model.checkActiveRepoIsNotNone()
            
            user = User()
            
            dialogs = UserDialogsFacade()
            if not dialogs.execUserDialog(
                user=user, gui=self._gui, dialogMode=UserDialog.LOGIN_MODE):
                return
            
            self._gui.model.loginUser(user.login, user.password)
                
        except Exception as ex:
            show_exc_info(self._gui, ex)
            
class LogoutUserActionHandler(AbstractActionHandler):
    def __init__(self, gui):
        super(LogoutUserActionHandler, self).__init__(gui)
        
    def handle(self):
        try:
            self._gui.model.user = None
        except Exception as ex:
            show_exc_info(self._gui, ex)



class ChangeUserPasswordActionHandler(AbstractActionHandler):
    def __init__(self, gui):
        super(ChangeUserPasswordActionHandler, self).__init__(gui)
        
    def handle(self):
        try:
            self._gui.model.checkActiveRepoIsNotNone()
            self._gui.model.checkActiveUserIsNotNone()
            
            user = self._gui.model.user
            
            dialogs = UserDialogsFacade()
            dialogExecOk, newPasswordHash = \
                dialogs.execChangeUserPasswordDialog(user=user, gui=self._gui)
            if not dialogExecOk:
                return
            
            uow = self._gui.model.repo.createUnitOfWork()
            try:
                command = ChangeUserPasswordCommand(user.login, newPasswordHash)
                uow.executeCommand(command)
            finally:
                uow.close()
                
            user.password = newPasswordHash
            
        except Exception as ex:
            show_exc_info(self._gui, ex)
        else:
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Operation completed."), STATUSBAR_TIMEOUT)
    
    
class CreateRepoActionHandler(AbstractActionHandler):
    def  __init__(self, gui):
        super(CreateRepoActionHandler, self).__init__(gui)
        
    def handle(self):
        try:
            dialogs = UserDialogsFacade()
            basePath = dialogs.getExistingDirectory(
                self._gui, self.tr("Choose a base path for new repository"))
            
            if not basePath:
                raise MsgException(
                    self.tr("You haven't chosen existent directory. Operation canceled."))
            
            # QFileDialog returns forward slashes in windows! Because of this 
            # the path should be normalized
            basePath = os.path.normpath(basePath)
            self._gui.model.repo = RepoMgr.createNewRepo(basePath)
            self._gui.model.user = self.__createDefaultUser()
        
        except Exception as ex:
            show_exc_info(self._gui, ex)
        
        
    def __createDefaultUser(self):
        self._gui.model.checkActiveRepoIsNotNone()
        
        defaultLogin = consts.DEFAULT_USER_LOGIN
        defaultPassword = helpers.computePasswordHash(consts.DEFAULT_USER_PASSWORD)
        user = User(login=defaultLogin, password=defaultPassword)
        
        uow = self._gui.model.repo.createUnitOfWork()
        try:
            uow.executeCommand(SaveNewUserCommand(user))
        finally:
            uow.close()
        return user


class CloseRepoActionHandler(AbstractActionHandler):
    def __init__(self, gui):
        super(CloseRepoActionHandler, self).__init__(gui)
        
    def handle(self):
        try:
            self._gui.model.checkActiveRepoIsNotNone()
            self._gui.model.repo = None
            self._gui.model.user = None
            
        except Exception as ex:
            show_exc_info(self._gui, ex)
                   
                   
class OpenRepoActionHandler(AbstractActionHandler):
    def __init__(self, gui):
        super(OpenRepoActionHandler, self).__init__(gui)
        
    def handle(self):
        try:
            dialogs = UserDialogsFacade()
            basePath = dialogs.getExistingDirectory(
                self._gui, self.tr("Choose a repository base path"))
            
            if not basePath:
                raise Exception(
                    self.tr("You haven't chosen existent directory. Operation canceled."))

            #QFileDialog returns forward slashes in windows! Because of this path should be normalized
            basePath = os.path.normpath(basePath)
            self._gui.model.repo = RepoMgr(basePath)
            self._gui.model.user = None
            self._gui.model.loginRecentUser()
            
        except LoginError:
            self.__letUserLoginByHimself()
                            
        except Exception as ex:
            show_exc_info(self._gui, ex)


    def __letUserLoginByHimself(self):
        user = User()
        dialogs = UserDialogsFacade()
        if not dialogs.execUserDialog(
            user=user, gui=self._gui, dialogMode=UserDialog.LOGIN_MODE):
            return
        try:
            self._gui.model.loginUser(user.login, user.password)
        except Exception as ex:
            show_exc_info(self._gui, ex)
        
        
class AddCurrentRepoToFavoritesActionHandler(AbstractActionHandler):
    
    def __init__(self, gui, favoriteReposStorage):
        super(AddCurrentRepoToFavoritesActionHandler, self).__init__(gui)
        self.__favoriteReposStorage = favoriteReposStorage
        
    def handle(self):
        try:
            self._gui.model.checkActiveRepoIsNotNone()
            self._gui.model.checkActiveUserIsNotNone()
            
            repoBasePath = self._gui.model.repo.base_path
            userLogin = self._gui.model.user.login
            
            #TODO: Maybe ask user for a repoAlias...
            self.__favoriteReposStorage.addRepoToFavorites(userLogin, 
                                                           repoBasePath, 
                                                           os.path.basename(repoBasePath))
            
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Current repository saved in favorites list."), STATUSBAR_TIMEOUT)
            self._emitHandlerSignal(HandlerSignals.LIST_OF_FAVORITE_REPOS_CHANGED)
            
        except Exception as ex:
            show_exc_info(self._gui, ex)

class RemoveCurrentRepoFromFavoritesActionHandler(AbstractActionHandler):
    
    def __init__(self, gui, favoriteReposStorage):
        super(RemoveCurrentRepoFromFavoritesActionHandler, self).__init__(gui)
        self.__favoriteReposStorage = favoriteReposStorage
        
    def handle(self):
        try:
            self._gui.model.checkActiveRepoIsNotNone()
            self._gui.model.checkActiveUserIsNotNone()
            
            repoBasePath = self._gui.model.repo.base_path
            userLogin = self._gui.model.user.login
            
            self.__favoriteReposStorage.removeRepoFromFavorites(userLogin, repoBasePath)
            
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Current repository removed from favorites list."), STATUSBAR_TIMEOUT)
            self._emitHandlerSignal(HandlerSignals.LIST_OF_FAVORITE_REPOS_CHANGED)
            
        except Exception as ex:
            show_exc_info(self._gui, ex)

            
        

class AddSingleItemActionHandler(AbstractActionHandler):
    def __init__(self, tool, dialogs):
        super(AddSingleItemActionHandler, self).__init__(tool)
        self.__dialogs = dialogs
        self.lastSavedItemId = None
        
    def handle(self):
        try:
            self._tool.checkActiveRepoIsNotNone()
            self._tool.checkActiveUserIsNotNone()
            
            item = Item(user_login=self._tool.user.login)
            
            #User can push Cancel button and do not select a file now
            #In such a case, Item will be added without file reference
            file = self.__dialogs.getOpenFileName(
                self._tool.gui, self.tr("Select a file to link with new Item."))
            
            if not is_none_or_empty(file):
                file = os.path.normpath(file)
                item.title = os.path.basename(file)
                item.data_ref = DataRef(type=DataRef.FILE, url=file)

            if not self.__dialogs.execItemDialog(
                item=item, gui=self._tool.gui, repo=self._tool.repo, dialogMode=ItemDialog.CREATE_MODE):
                return
            
            uow = self._tool.repo.createUnitOfWork()
            try:
                srcAbsPath = None
                dstRelPath = None
                if item.data_ref is not None:
                    srcAbsPath = item.data_ref.srcAbsPath
                    dstRelPath = item.data_ref.dstRelPath

                cmd = SaveNewItemCommand(item, srcAbsPath, dstRelPath)
                thread = BackgrThread(self._tool.gui, uow.executeCommand, cmd)
                
                self.__dialogs.startThreadWithWaitDialog(
                    thread, self._tool.gui, indeterminate=True)
                
                self.lastSavedItemId = thread.result
                
            finally:
                uow.close()
                
        except Exception as ex:
            show_exc_info(self._tool.gui, ex)
            
        else:
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE, 
                self.tr("Item added to repository."), consts.STATUSBAR_TIMEOUT)
            self._emitHandlerSignal(HandlerSignals.ITEM_CREATED)


class AddManyItemsAbstractActionHandler(AbstractActionHandler):
    def __init__(self, tool, dialogs):
        super(AddManyItemsAbstractActionHandler, self).__init__(tool)
        self._dialogs = dialogs
        self._createdObjectsCount = 0
        self._errorLog = []
        self.lastSavedItemIds = []
    
    def _startWorkerThread(self, items):
        thread = CreateGroupOfItemsThread(self._tool.gui, self._tool.repo, items)
        
        self._dialogs.startThreadWithWaitDialog(
                thread, self._tool.gui, indeterminate=False)
            
        self._createdObjectsCount = thread.created_objects_count
        self._errorLog = thread.error_log
        self.lastSavedItemIds = thread.lastSavedItemIds
        
 
class AddManyItemsActionHandler(AddManyItemsAbstractActionHandler):
    def __init__(self, tool, dialogs):
        super(AddManyItemsActionHandler, self).__init__(tool, dialogs)
        
    def handle(self):
        try:
            self._tool.checkActiveRepoIsNotNone()
            self._tool.checkActiveUserIsNotNone()
            
            files = self._dialogs.getOpenFileNames(self._tool.gui, self.tr("Select file to add"))
            if len(files) == 0:
                raise MsgException(self.tr("No files chosen. Operation cancelled."))
            
            items = []
            for file in files:
                file = os.path.normpath(file)
                item = Item(user_login=self._tool.user.login)
                item.title = os.path.basename(file)
                item.data_ref = DataRef(type=DataRef.FILE, url=file) #DataRef.url can be changed in ItemsDialog
                item.data_ref.srcAbsPath = file
                items.append(item)
            
            if not self._dialogs.execItemsDialog(
                items, self._tool.gui, self._tool.repo, ItemsDialog.CREATE_MODE, sameDstPath=True):
                return
            
            self._startWorkerThread(items)
            
            self._emitHandlerSignal(HandlerSignals.ITEM_CREATED)
                
        except Exception as ex:
            show_exc_info(self._tool.gui, ex)
            
        finally:
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE, 
                self.tr("Operation completed. Stored {} files, skipped {} files.")
                    .format(self._createdObjectsCount, len(self._errorLog)))
            
        
        
class AddManyItemsRecursivelyActionHandler(AddManyItemsAbstractActionHandler):
    def __init__(self, tool, dialogs):
        super(AddManyItemsRecursivelyActionHandler, self).__init__(tool, dialogs)
        
    def handle(self):
        '''
            Add many items recursively from given directory to the repo.
        '''
        try:
            self._tool.checkActiveRepoIsNotNone()
            self._tool.checkActiveUserIsNotNone()
            
            dirPath = self._dialogs.getExistingDirectory(
                self._tool.gui, self.tr("Select single existing directory"))
            if not dirPath:
                raise MsgException(self.tr("Directory is not chosen. Operation cancelled."))
                        
            dirPath = os.path.normpath(dirPath)
            
            items = []
            for root, dirs, files in os.walk(dirPath):
                if os.path.relpath(root, dirPath) == ".reggata":
                    continue
                for file in files:
                    item = Item(title=file, user_login=self._tool.user.login)
                    srcAbsPath = os.path.join(root, file)
                    item.data_ref = DataRef(type=DataRef.FILE, url=srcAbsPath) #DataRef.url can be changed in ItemsDialog
                    item.data_ref.srcAbsPath = srcAbsPath
                    item.data_ref.srcAbsPathToRecursionRoot = dirPath
                    # item.data_ref.dstRelPath will be set by ItemsDialog
                    items.append(item)
            
            if not self._dialogs.execItemsDialog(
                items, self._tool.gui, self._tool.repo, ItemsDialog.CREATE_MODE, sameDstPath=False):
                return
                
            self._startWorkerThread(items)
            self._emitHandlerSignal(HandlerSignals.ITEM_CREATED)
                
        except Exception as ex:
            show_exc_info(self._tool.gui, ex)
            
        finally:
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE, 
                self.tr("Operation completed. Stored {} files, skipped {} files.")
                    .format(self._createdObjectsCount, len(self._errorLog)))
            



class EditItemActionHandler(AbstractActionHandler):
    def __init__(self, tool, dialogs):
        super(EditItemActionHandler, self).__init__(tool)
        self._dialogs = dialogs
        
    def handle(self):
        try:
            self._tool.checkActiveRepoIsNotNone()
            self._tool.checkActiveUserIsNotNone()            
            
            itemIds = self._tool.gui.selectedItemIds()
            if len(itemIds) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            if len(itemIds) > 1:
                self.__editManyItems(itemIds)
            else:
                self.__editSingleItem(itemIds.pop())
                            
        except Exception as ex:
            show_exc_info(self._tool.gui, ex)
            
        else:
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE, 
                                    self.tr("Editing done."), STATUSBAR_TIMEOUT)
            self._emitHandlerSignal(HandlerSignals.ITEM_CHANGED)
            
    
    def __editSingleItem(self, itemId):
        uow = self._tool.repo.createUnitOfWork()
        try:
            item = uow.executeCommand(GetExpungedItemCommand(itemId))
            
            if not self._dialogs.execItemDialog(
                item=item, gui=self._tool.gui, repo=self._tool.repo, dialogMode=ItemDialog.EDIT_MODE):
                return
            
            cmd = UpdateExistingItemCommand(item, self._tool.user.login)
            uow.executeCommand(cmd)
        finally:
            uow.close()
    
    def __editManyItems(self, itemIds):
        uow = self._tool.repo.createUnitOfWork()
        try:
            items = []
            for itemId in itemIds:
                items.append(uow.executeCommand(GetExpungedItemCommand(itemId)))
            
            if not self._dialogs.execItemsDialog(
                items, self._tool.gui, self._tool.repo, ItemsDialog.EDIT_MODE, sameDstPath=True):
                return
            
            thread = UpdateGroupOfItemsThread(self._tool.gui, self._tool.repo, items)
            self._dialogs.startThreadWithWaitDialog(thread, self._tool.gui, indeterminate=False)
                
        finally:
            uow.close()

class RebuildItemThumbnailActionHandler(AbstractActionHandler):
    def __init__(self, tool):
        super(RebuildItemThumbnailActionHandler, self).__init__(tool)
    
    def handle(self):
        
        def refresh(percent, row):
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Rebuilding thumbnails ({0}%)").format(percent))
            self._emitHandlerSignal(HandlerSignals.RESET_SINGLE_ROW, row)
            QtCore.QCoreApplication.processEvents()
        
        try:
            self._tool.checkActiveRepoIsNotNone()
            self._tool.checkActiveUserIsNotNone()
                    
            rows = self._tool.gui.selectedRows()
            if len(rows) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            
            uow = self._tool.repo.createUnitOfWork()
            try:
                items = []
                for row in rows:
                    item = self._tool.gui.itemAtRow(row)
                    item.table_row = row
                    items.append(item)
                 
                thread = ThumbnailBuilderThread(
                    self._tool.gui, self._tool.repo, items, self._tool.itemsLock, 
                    rebuild=True)
                
                self.connect(thread, QtCore.SIGNAL("exception"), 
                    lambda exc_info: show_exc_info(
                        self._tool.gui, exc_info[1], details=format_exc_info(*exc_info)))
                self.connect(thread, QtCore.SIGNAL("progress"), 
                    lambda percents, row: refresh(percents, row))
                self.connect(thread, QtCore.SIGNAL("finished"), 
                    lambda: self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE, 
                        self.tr("Rebuild thumbnails is done.")))
                thread.start()
                    
            finally:
                uow.close()
            
        except Exception as ex:
            show_exc_info(self._tool.gui, ex)
            
class DeleteItemActionHandler(AbstractActionHandler):
    def __init__(self, tool, dialogs):
        super(DeleteItemActionHandler, self).__init__(tool)
        self._dialogs = dialogs
    
    def handle(self):
        try:
            self._tool.checkActiveRepoIsNotNone()
            self._tool.checkActiveUserIsNotNone()
                        
            itemIds = self._tool.gui.selectedItemIds()
            if len(itemIds) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            mbResult = self._dialogs.execMessageBox(self._tool.gui,
                text=self.tr("Do you really want to delete {} selected file(s)?").format(len(itemIds)),
                buttons=[QtGui.QMessageBox.Yes, QtGui.QMessageBox.No])
            if mbResult != QtGui.QMessageBox.Yes:
                raise CancelOperationError()
            
            thread = DeleteGroupOfItemsThread(
                self._tool.gui, self._tool.repo, itemIds, self._tool.user.login)
            
            self._dialogs.startThreadWithWaitDialog(thread, self._tool.gui, indeterminate=False)
                
            if thread.errors > 0:
                self._dialogs.execMessageBox(self._tool.gui,
                    text=self.tr("There were {0} errors.").format(thread.errors),
                    detailedText=thread.detailed_message)
                
        except CancelOperationError:
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Operation cancelled."), STATUSBAR_TIMEOUT)
            
        except Exception as ex:
            show_exc_info(self._tool.gui, ex)
            
        else:
            #TODO: display information about how many items were deleted
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Operation completed."), STATUSBAR_TIMEOUT)
            self._emitHandlerSignal(HandlerSignals.ITEM_DELETED)
            

class OpenItemActionHandler(AbstractActionHandler):
    def __init__(self, tool, extAppMgr):
        super(OpenItemActionHandler, self).__init__(tool)
        self._extAppMgr = extAppMgr
    
    def handle(self):
        try:
            selRows = self._tool.gui.selectedRows()
            if len(selRows) != 1:
                raise MsgException(self.tr("Select one item, please."))
            
            dataRef = self._tool.gui.itemAtRow(selRows.pop()).data_ref
            
            if dataRef is None or dataRef.type != DataRef.FILE:
                raise MsgException(self.tr("This action can be applied only to the items linked with files."))
            
            self._extAppMgr.invoke(os.path.join(self._tool.repo.base_path, dataRef.url))
            
        except Exception as ex:
            show_exc_info(self._tool.gui, ex)
            
        else:
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE, 
                self.tr("Done."), STATUSBAR_TIMEOUT)
    
    
class OpenItemWithInternalImageViewerActionHandler(AbstractActionHandler):
    def __init__(self, tool):
        super(OpenItemWithInternalImageViewerActionHandler, self).__init__(tool)
        
    def handle(self):
        try:
            self._tool.checkActiveRepoIsNotNone()
            self._tool.checkActiveUserIsNotNone()
            
            rows = self._tool.gui.selectedRows()
            if len(rows) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            startIndex = 0 #This is the index of the first image to show
            items = []
            if len(rows) == 1:
                #If there is only one selected item, pass to viewer all items in this table model
                for row in range(self._tool.gui.rowCount()):
                    items.append(self._tool.gui.itemAtRow(row))
                startIndex = rows.pop()
                
            else:
                for row in rows:
                    items.append(self._tool.gui.itemAtRow(row))
            
            iv = ImageViewer(self._tool.gui, self._tool.widgetsUpdateManager,
                             self._tool.repo, self._tool.user.login,
                             items, startIndex)
            iv.show()
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Done."), STATUSBAR_TIMEOUT)
            
        except Exception as ex:
            show_exc_info(self._tool.gui, ex)
    
    
class ExportItemsToM3uAndOpenItActionHandler(AbstractActionHandler):
    def __init__(self, tool, extAppMgr):
        super(ExportItemsToM3uAndOpenItActionHandler, self).__init__(tool)
        self._extAppMgr = extAppMgr
        
    def handle(self):
        try:
            self._tool.checkActiveRepoIsNotNone()
            self._tool.checkActiveUserIsNotNone()
            
            rows = self._tool.gui.selectedRows()
            if len(rows) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            tmpDir = UserConfig().get("tmp_dir", consts.DEFAULT_TMP_DIR)
            if not os.path.exists(tmpDir):
                os.makedirs(tmpDir)
                
            m3uFilename = str(os.getpid()) + self._tool.user.login + str(time.time()) + ".m3u"
            with open(os.path.join(tmpDir, m3uFilename), "wt") as m3uFile:
                for row in rows:
                    m3uFile.write(
                        os.path.join(self._tool.repo.base_path, 
                                     self._tool.gui.itemAtRow(row).data_ref.url) + os.linesep)                                            
                    
            self._extAppMgr.invoke(os.path.join(tmpDir, m3uFilename))
            
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Done."), STATUSBAR_TIMEOUT)
            
        except Exception as ex:
            show_exc_info(self._tool.gui, ex)
            

class OpenItemWithExternalFileManagerActionHandler(AbstractActionHandler):
    def __init__(self, gui):
        super(OpenItemWithExternalFileManagerActionHandler, self).__init__(gui)
        
    def handle(self):
        try:
            sel_rows = self._gui.selectedRows()
            if len(sel_rows) != 1:
                raise MsgException(self.tr("Select one item, please."))
            
            data_ref = self._gui.itemAtRow(sel_rows.pop()).data_ref
            
            if data_ref is None or data_ref.type != DataRef.FILE:
                raise MsgException(
                    self.tr("This action can be applied only to the items linked with files."))
            
            eam = ExtAppMgr()
            eam.external_file_manager(os.path.join(self._gui.model.repo.base_path, data_ref.url))
                        
        except Exception as ex:
            show_exc_info(self._gui, ex)

class ExportItemsActionHandler(AbstractActionHandler):
    ''' Exports selected items with all their metadata (tags, fiedls) and
    all the referenced files. Items are packed in zip archive and later 
    they can be imported to another repository.
    '''
    def __init__(self, gui):
        super(ExportItemsActionHandler, self).__init__(gui)
        
    def handle(self):
        try:
            self._gui.model.checkActiveRepoIsNotNone()
            
            itemIds = self._gui.selectedItemIds()
            if len(itemIds) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            dialogs = UserDialogsFacade()
            exportFilename = dialogs.getSaveFileName(self._gui, self.tr('Save data as..')) 
            if not exportFilename:
                raise MsgException(self.tr("You haven't chosen a file. Operation canceled."))
            
            thread = ExportItemsThread(self._gui, self._gui.model.repo, itemIds, exportFilename)
                                    
            wd = WaitDialog(self._gui)
            self.connect(thread, QtCore.SIGNAL("progress"), wd.set_progress)
            self.connect(thread, QtCore.SIGNAL("finished"), wd.reject)
            self.connect(thread, QtCore.SIGNAL("exception"), wd.exception)
            wd.startWithWorkerThread(thread)
            

        except Exception as ex:
            show_exc_info(self._gui, ex)
        else:
            #TODO: display information about how many items were exported
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Operation completed."), STATUSBAR_TIMEOUT)

class ImportItemsActionHandler(AbstractActionHandler):
    ''' Imports previously exported items.
    '''
    def __init__(self, gui):
        super(ImportItemsActionHandler, self).__init__(gui)
    
    def handle(self):
        try:
            self._gui.model.checkActiveRepoIsNotNone()
            self._gui.model.checkActiveUserIsNotNone()
            
            dialogs = UserDialogsFacade()
            
            importFromFilename = dialogs.getOpenFileName(self._gui, self.tr('Open reggata export file..'))
            if not importFromFilename:
                raise MsgException(self.tr("You haven't chosen a file. Operation canceled."))
            
            thread = ImportItemsThread(self._gui, self._gui.model.repo, importFromFilename, 
                                       self._gui.model.user.login)
                                    
            wd = WaitDialog(self._gui)
            self.connect(thread, QtCore.SIGNAL("progress"), wd.set_progress)
            self.connect(thread, QtCore.SIGNAL("finished"), wd.reject)
            self.connect(thread, QtCore.SIGNAL("exception"), wd.exception)
            wd.startWithWorkerThread(thread)

        except Exception as ex:
            show_exc_info(self._gui, ex)
        else:
            self._emitHandlerSignal(HandlerSignals.ITEM_CREATED)
            #TODO: display information about how many items were imported
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Operation completed."), STATUSBAR_TIMEOUT)
            
        

class ExportItemsFilesActionHandler(AbstractActionHandler):
    def __init__(self, gui):
        super(ExportItemsFilesActionHandler, self).__init__(gui)
        
    def handle(self):
        try:
            self._gui.model.checkActiveRepoIsNotNone()
            
            item_ids = self._gui.selectedItemIds()
            if len(item_ids) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            dialogs = UserDialogsFacade()
            export_dir_path = dialogs.getExistingDirectory(
                self._gui, self.tr("Choose a directory path to export files into."))
            
            if not export_dir_path:
                raise MsgException(self.tr("You haven't chosen existent directory. Operation canceled."))
            
            thread = ExportItemsFilesThread(self._gui, self._gui.model.repo, item_ids, export_dir_path)
                                    
            wd = WaitDialog(self._gui)
            self.connect(thread, QtCore.SIGNAL("progress"), wd.set_progress)
            self.connect(thread, QtCore.SIGNAL("finished"), wd.reject)
            self.connect(thread, QtCore.SIGNAL("exception"), wd.exception)
            wd.startWithWorkerThread(thread)
            

        except Exception as ex:
            show_exc_info(self._gui, ex)
        else:
            #TODO: display information about how many files were copied
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Operation completed."), STATUSBAR_TIMEOUT)

class ExportItemsFilePathsActionHandler(AbstractActionHandler):
    def __init__(self, gui):
        super(ExportItemsFilePathsActionHandler, self).__init__(gui)
        
    def handle(self):
        try:
            self._gui.model.checkActiveRepoIsNotNone()
            
            rows = self._gui.selectedRows()
            if len(rows) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            dialogs = UserDialogsFacade()
            exportFilename = dialogs.getSaveFileName(self._gui, self.tr('Save results in a file.'))
            if not exportFilename:
                raise MsgException(self.tr("Operation canceled."))
            
            file = open(exportFilename, "w", newline='')
            for row in rows:
                item = self._gui.itemAtRow(row)
                if item.is_data_ref_null():
                    continue
                textline = self._gui.model.repo.base_path + \
                    os.sep + self._gui.itemAtRow(row).data_ref.url + os.linesep
                file.write(textline)
            file.close()

        except Exception as ex:
            show_exc_info(self._gui, ex)
        else:
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Operation completed."), STATUSBAR_TIMEOUT)


class FixItemIntegrityErrorActionHandler(AbstractActionHandler):
    def __init__(self, gui, strategy):
        super(FixItemIntegrityErrorActionHandler, self).__init__(gui)
        self.__strategy = strategy
    
    def handle(self):
        
        def refresh(percent, row):
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Integrity fix {0}%").format(percent))
            
            #TODO: Have to replace this direct updates with emitting some specific signals..
            self._gui.resetSingleRow(row)
            QtCore.QCoreApplication.processEvents()
        
        try:
            self._gui.model.checkActiveRepoIsNotNone()
            self._gui.model.checkActiveUserIsNotNone()
            
            rows = self._gui.selectedRows()
            if len(rows) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            items = []
            for row in rows:
                item = self._gui.itemAtRow(row) 
                item.table_row = row
                items.append(item)
                        
            thread = ItemIntegrityFixerThread(
                self._gui, self._gui.model.repo, items, self._gui.model.itemsLock, self.__strategy, self._gui.model.user.login)
            
            self.connect(thread, QtCore.SIGNAL("progress"),
                         lambda percents, row: refresh(percents, row))
            self.connect(thread, QtCore.SIGNAL("finished"),
                         lambda: self._emitHandlerSignal(
                                    HandlerSignals.STATUS_BAR_MESSAGE,
                                    self.tr("Integrity fixing is done."))
                         )
            self.connect(thread, QtCore.SIGNAL("exception"), 
                         lambda exc_info: show_exc_info(self._gui, exc_info[1], details=format_exc_info(*exc_info)))
            
            
            thread.start()
            
        except Exception as ex:
            show_exc_info(self._gui, ex)

class CheckItemIntegrityActionHandler(AbstractActionHandler):
    def __init__(self, gui):
        super(CheckItemIntegrityActionHandler, self).__init__(gui)
    
    def handle(self):
        def refresh(percent, row):
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Integrity check {0}%").format(percent))            
            
            #TODO: Have to replace this direct updates with emitting some specific signals..
            self._gui.resetSingleRow(row)
            QtCore.QCoreApplication.processEvents()
        
        try:
            self._gui.model.checkActiveRepoIsNotNone()
            self._gui.model.checkActiveUserIsNotNone()            
            
            rows = self._gui.selectedRows()
            if len(rows) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            items = []
            for row in rows:
                item = self._gui.itemAtRow(row)
                item.table_row = row
                items.append(item)
             
            thread = ItemIntegrityCheckerThread(
                self._gui, self._gui.model.repo, items, self._gui.model.itemsLock)
            self.connect(thread, QtCore.SIGNAL("progress"), 
                         lambda percents, row: refresh(percents, row))
            self.connect(thread, QtCore.SIGNAL("finished"), 
                         lambda error_count: self._emitHandlerSignal(
                             HandlerSignals.STATUS_BAR_MESSAGE,
                             self.tr("Integrity check is done. {0} Items with errors.")
                                 .format(error_count))
                         )
            thread.start()
            
        except Exception as ex:
            show_exc_info(self._gui, ex)

    
class ShowAboutDialogActionHandler(AbstractActionHandler):
    def __init__(self, gui):
        super(ShowAboutDialogActionHandler, self).__init__(gui)
        
    def handle(self):
        try:
            ad = AboutDialog(self._gui)
            ad.exec_()
        except Exception as ex:
            show_exc_info(self._gui, ex)
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
            
            currentUser = self._tool.user
            assert currentUser is not None
            
            self._tool.repo = RepoMgr(repoBasePath)
            
            try:
                self._tool.loginUser(currentUser.login, currentUser.password)
                self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                    self.tr("Repository opened. Login succeded."), STATUSBAR_TIMEOUT)
                
            except LoginError:
                self._tool.user = None
                self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                    self.tr("Repository opened. Login failed."), STATUSBAR_TIMEOUT)
        
        except Exception as ex:
            show_exc_info(self._tool.gui, ex)
        
        
    
