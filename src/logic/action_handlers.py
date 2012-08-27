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
from gui.user_dialog import UserDialog
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


class HandlerSignals():
    '''Named constants in this class is not the signal names, but the signal types.
    They are arguments of the following signals: handlerSignal, handlerSignals.
    handlerSignal accepts single signal type. handlerSignals accepts a list of
    signal types. See also WidgetsUpdateManager, ActionHandlerStorage and
    AbstractActionHandler classes.
    '''
    
    ITEM_CREATED = "itemCreated"
    ITEM_CHANGED = "itemChanged"
    ITEM_DELETED = "itemDeleted"
    
    @staticmethod
    def allSignals():
        return [HandlerSignals.ITEM_CREATED, HandlerSignals.ITEM_CHANGED, HandlerSignals.ITEM_DELETED]


class AbstractActionHandler(QtCore.QObject):
    def __init__(self, gui=None):
        super(AbstractActionHandler, self).__init__()
        self._gui = gui
        
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
        self.discconnect(self, QtCore.SIGNAL("handlerSignals"), \
                     widgetsUpdateManager.onHandlerSignals)
    
class CreateUserActionHandler(AbstractActionHandler):
    def __init__(self, gui):
        super(CreateUserActionHandler, self).__init__(gui)
        
    def handle(self):
        try:
            self._gui.checkActiveRepoIsNotNone()
            
            u = UserDialog(User(), self._gui, UserDialog.CREATE_MODE)
            if not u.exec_():
                return
            
            uow = self._gui.active_repo.create_unit_of_work()
            try:
                uow.executeCommand(SaveNewUserCommand(u.user))
                self._gui.active_user = u.user
            finally:
                uow.close()
                
        except Exception as ex:
            show_exc_info(self._gui, ex)

class LoginUserActionHandler(AbstractActionHandler):
    def __init__(self, gui):
        super(LoginUserActionHandler, self).__init__(gui)
        
    def handle(self):
        try:
            self._gui.checkActiveRepoIsNotNone()
            
            ud = UserDialog(User(), self._gui, mode=UserDialog.LOGIN_MODE)
            if not ud.exec_():
                return                     
            
            self._gui.loginUser(ud.user.login, ud.user.password)
                
        except Exception as ex:
            show_exc_info(self._gui, ex)
            
class LogoutUserActionHandler(AbstractActionHandler):
    def __init__(self, gui):
        super(LogoutUserActionHandler, self).__init__(gui)
        
    def handle(self):
        try:
            self._gui.active_user = None
        except Exception as ex:
            show_exc_info(self._gui, ex)



class ChangeUserPasswordActionHandler(AbstractActionHandler):
    def __init__(self, gui):
        super(ChangeUserPasswordActionHandler, self).__init__(gui)
        
    def handle(self):
        try:
            self._gui.checkActiveRepoIsNotNone()
            self._gui.checkActiveUserIsNotNone()
            
            user = self._gui.active_user
            dialog = ChangeUserPasswordDialog(self._gui, user)
            if not dialog.exec_():
                return
            
            uow = self._gui.active_repo.create_unit_of_work()
            try:
                command = ChangeUserPasswordCommand(user.login, dialog.newPasswordHash)
                uow.executeCommand(command)
            finally:
                uow.close()
            
        except Exception as ex:
            show_exc_info(self._gui, ex)
        else:
            self._gui.showMessageOnStatusBar(self.tr("Operation completed."), STATUSBAR_TIMEOUT)
    
    
class CreateRepoActionHandler(AbstractActionHandler):
    def  __init__(self, gui):
        super(CreateRepoActionHandler, self).__init__(gui)
        
    def handle(self):
        try:
            basePath = QtGui.QFileDialog.getExistingDirectory(
                self._gui, self.tr("Choose a base path for new repository"))
            if not basePath:
                raise MsgException(
                    self.tr("You haven't chosen existent directory. Operation canceled."))
            
            # QFileDialog returns forward slashes in windows! Because of this 
            # the path should be normalized
            basePath = os.path.normpath(basePath)
            self._gui.active_repo = RepoMgr.createNewRepo(basePath)
            self._gui.active_user = self.__createDefaultUser()
        
        except Exception as ex:
            show_exc_info(self._gui, ex)
        
        
    def __createDefaultUser(self):
        self._gui.checkActiveRepoIsNotNone()
        
        defaultLogin = consts.DEFAULT_USER_LOGIN
        defaultPassword = helpers.computePasswordHash(consts.DEFAULT_USER_PASSWORD)
        user = User(login=defaultLogin, password=defaultPassword)
        
        uow = self._gui.active_repo.create_unit_of_work()
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
            self._gui.checkActiveRepoIsNotNone()
            self._gui.active_repo = None
            self._gui.active_user = None
        except Exception as ex:
            show_exc_info(self._gui, ex)
                   
                   
class OpenRepoActionHandler(AbstractActionHandler):
    def __init__(self, gui):
        super(OpenRepoActionHandler, self).__init__(gui)
        
    def handle(self):
        try:
            base_path = QtGui.QFileDialog.getExistingDirectory(
                self._gui, self.tr("Choose a repository base path"))
            
            if not base_path:
                raise Exception(
                    self.tr("You haven't chosen existent directory. Operation canceled."))

            #QFileDialog returns forward slashes in windows! Because of this path should be normalized
            base_path = os.path.normpath(base_path)
            self._gui.active_repo = RepoMgr(base_path)
            self._gui.active_user = None
            self._gui.loginRecentUser()
            
        except LoginError:
            ud = UserDialog(User(), self._gui, mode=UserDialog.LOGIN_MODE)
            if not ud.exec_():
                return
            
            self._gui.loginUser(ud.user.login, ud.user.password)
                            
        except Exception as ex:
            show_exc_info(self._gui, ex)


class AddSingleItemActionHandler(AbstractActionHandler):
    def __init__(self, gui):
        super(AddSingleItemActionHandler, self).__init__(gui)
        
    def handle(self):
        try:
            self._gui.checkActiveRepoIsNotNone()
            self._gui.checkActiveUserIsNotNone()
            
            item = Item(user_login=self._gui.active_user.login)
            
            #User can push Cancel button and do not select a file now
            #In such a case, Item will be added without file reference
            file = self._gui.getOpenFileName(self.tr("Select a file to link with new Item."))
            
            if not is_none_or_empty(file):
                file = os.path.normpath(file)
                item.title = os.path.basename(file)
                item.data_ref = DataRef(type=DataRef.FILE, url=file)
            
            
            completer = Completer(self._gui.active_repo, self._gui)
            dialog = ItemDialog(self._gui, item, ItemDialog.CREATE_MODE, completer=completer)
            if not dialog.exec_():
                return
            
            uow = self._gui.active_repo.create_unit_of_work()
            try:
                srcAbsPath = None
                dstRelPath = None
                if dialog.item.data_ref is not None:
                    srcAbsPath = dialog.item.data_ref.srcAbsPath
                    dstRelPath = dialog.item.data_ref.dstRelPath

                cmd = SaveNewItemCommand(dialog.item, srcAbsPath, dstRelPath)
                thread = BackgrThread(self._gui, uow.executeCommand, cmd)
                
                wd = WaitDialog(self._gui, indeterminate=True)
                self.connect(thread, QtCore.SIGNAL("finished"), wd.reject)
                self.connect(thread, QtCore.SIGNAL("exception"), wd.exception)
                wd.startWithWorkerThread(thread)
        
            finally:
                uow.close()
                
                
        except Exception as ex:
            show_exc_info(self._gui, ex)
        else:
            self._gui.showMessageOnStatusBar(self.tr("Operation completed."), STATUSBAR_TIMEOUT)
            self.emit(QtCore.SIGNAL("handlerSignal"), HandlerSignals.ITEM_CREATED)

class AddManyItemsAbstractActionHandler(AbstractActionHandler):
    def __init__(self, gui):
        super(AddManyItemsAbstractActionHandler, self).__init__(gui)
        
        self._createdObjectsCount = 0
        self._errorLog = []
    
    def _startWorkerThread(self, items):
        thread = CreateGroupIfItemsThread(self._gui, self._gui.active_repo, items)
        
        wd = WaitDialog(self._gui)
        self.connect(thread, QtCore.SIGNAL("finished"), wd.reject)
        self.connect(thread, QtCore.SIGNAL("exception"), wd.exception)
        self.connect(thread, QtCore.SIGNAL("progress"), wd.set_progress)
        wd.startWithWorkerThread(thread)
            
        self._createdObjectsCount = thread.created_objects_count
        self._errorLog = thread.error_log
        
 
class AddManyItemsActionHandler(AddManyItemsAbstractActionHandler):
    def __init__(self, gui):
        super(AddManyItemsActionHandler, self).__init__(gui)
        
    def handle(self):
        try:
            self._gui.checkActiveRepoIsNotNone()
            self._gui.checkActiveUserIsNotNone()
            
            files = self._gui.getOpenFileNames(self.tr("Select file to add"))
            if len(files) == 0:
                raise MsgException(self.tr("No files chosen. Operation cancelled."))
            
            items = []
            for file in files:
                file = os.path.normpath(file)
                item = Item(user_login=self._gui.active_user.login)
                item.title = os.path.basename(file)
                item.data_ref = DataRef(type=DataRef.FILE, url=None) #DataRef.url doesn't important here
                item.data_ref.srcAbsPath = file
                items.append(item)
            
            completer = Completer(self._gui.active_repo, self._gui)
            repoBasePath = self._gui.active_repo.base_path
            d = ItemsDialog(self._gui, repoBasePath, items, ItemsDialog.CREATE_MODE, 
                            same_dst_path=True, completer=completer)
            if not d.exec_():
                return
            
            self._startWorkerThread(items)
                
        except Exception as ex:
            show_exc_info(self._gui, ex)
        finally:
            self._gui.showMessageOnStatusBar(self.tr("Operation completed. Stored {} files, skipped {} files.").format(self._createdObjectsCount, len(self._errorLog)))
            self.emit(QtCore.SIGNAL("handlerSignal"), HandlerSignals.ITEM_CREATED)
        
        
class AddManyItemsRecursivelyActionHandler(AddManyItemsAbstractActionHandler):
    def __init__(self, gui):
        super(AddManyItemsRecursivelyActionHandler, self).__init__(gui)
        
    def handle(self):
        ''' Add many items recursively from given directory to the repo.
        '''
        try:
            self._gui.checkActiveRepoIsNotNone()
            self._gui.checkActiveUserIsNotNone()
            
            dir = self._gui.getExistingDirectory(self.tr("Select sigle existing directory"))
            #dir = QtGui.QFileDialog.getExistingDirectory(self._gui, self.tr("Select one directory"))
            if not dir:
                raise MsgException(self.tr("Directory is not chosen. Operation cancelled."))
                        
            dir = os.path.normpath(dir)
            
            items = []
            for root, dirs, files in os.walk(dir):
                if os.path.relpath(root, dir) == ".reggata":
                    continue
                for file in files:
                    item = Item(title=file, user_login=self._gui.active_user.login)
                    item.data_ref = DataRef(type=DataRef.FILE, url=None) #DataRef.url doesn't important here
                    item.data_ref.srcAbsPath = os.path.join(root, file)
                    item.data_ref.srcAbsPathToRecursionRoot = dir
                    # item.data_ref.dstRelPath will be set by ItemsDialog
                    items.append(item)
            
            completer = Completer(self._gui.active_repo, self._gui)
            repoBasePath = self._gui.active_repo.base_path
            d = ItemsDialog(self._gui, repoBasePath, items, ItemsDialog.CREATE_MODE, 
                            same_dst_path=False, completer=completer)
            if not d.exec_():
                return
                
            self._startWorkerThread(items)
                
        except Exception as ex:
            show_exc_info(self._gui, ex)
        finally:
            self._gui.showMessageOnStatusBar(self.tr("Operation completed. Stored {} files, skipped {} files.").format(self._createdObjectsCount, len(self._errorLog)))
            self.emit(QtCore.SIGNAL("handlerSignal"), HandlerSignals.ITEM_CREATED)
            
            
            




class EditItemActionHandler(AbstractActionHandler):
    def __init__(self, gui):
        super(EditItemActionHandler, self).__init__(gui)
        
    def handle(self):
        try:
            self._gui.checkActiveRepoIsNotNone()
            self._gui.checkActiveUserIsNotNone()            
            
            itemIds = self._gui.selectedItemIds()
            if len(itemIds) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            if len(itemIds) > 1:
                self.__editManyItems(itemIds)
            else:
                self.__editSingleItem(itemIds.pop())
                            
        except Exception as ex:
            show_exc_info(self._gui, ex)
        else:
            self._gui.showMessageOnStatusBar(self.tr("Operation completed."), STATUSBAR_TIMEOUT)
            self.emit(QtCore.SIGNAL("handlerSignal"), HandlerSignals.ITEM_CHANGED)
            
    
    def __editSingleItem(self, itemId):
        uow = self._gui.active_repo.create_unit_of_work()
        try:
            item = uow.executeCommand(GetExpungedItemCommand(itemId))
            completer = Completer(self._gui.active_repo, self._gui)
            item_dialog = ItemDialog(self._gui, item, ItemDialog.EDIT_MODE, completer=completer)
            if not item_dialog.exec_():
                return
            cmd = UpdateExistingItemCommand(item, self._gui.active_user.login)
            uow.executeCommand(cmd)
        finally:
            uow.close()
    
    def __editManyItems(self, itemIds):
        uow = self._gui.active_repo.create_unit_of_work()
        try:
            items = []
            for itemId in itemIds:
                items.append(uow.executeCommand(GetExpungedItemCommand(itemId)))
            completer = Completer(self._gui.active_repo, self._gui)
            repoBasePath = self._gui.active_repo.base_path
            dlg = ItemsDialog(self._gui, repoBasePath, items, ItemsDialog.EDIT_MODE, completer=completer)
            if not dlg.exec_():
                return
            
            thread = UpdateGroupOfItemsThread(self._gui, self._gui.active_repo, items)
                    
            wd = WaitDialog(self._gui)
            self.connect(thread, QtCore.SIGNAL("finished"), wd.reject)
            self.connect(thread, QtCore.SIGNAL("exception"), wd.exception)
            self.connect(thread, QtCore.SIGNAL("progress"), wd.set_progress)
            wd.startWithWorkerThread(thread)     
                
        finally:
            uow.close()

class RebuildItemThumbnailActionHandler(AbstractActionHandler):
    def __init__(self, gui):
        super(RebuildItemThumbnailActionHandler, self).__init__(gui)
    
    def handle(self):
        
        def refresh(percent, row):
            self._gui.showMessageOnStatusBar(self.tr("Rebuilding thumbnails ({0}%)").format(percent))
            
            #TODO: Have to replace this direct updates with emitting some specific signals..
            self._gui.resetSingleRow(row)
            QtCore.QCoreApplication.processEvents()
        
        try:
            self._gui.checkActiveRepoIsNotNone()
            self._gui.checkActiveUserIsNotNone()
                    
            rows = self._gui.selectedRows()
            if len(rows) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            
            uow = self._gui.active_repo.create_unit_of_work()
            try:
                items = []
                for row in rows:                    
                    self._gui.itemAtRow(row).table_row = row
                    items.append(self._gui.model.items[row])
                 
                thread = ThumbnailBuilderThread(
                    self._gui, self._gui.active_repo, items, self._gui.items_lock, rebuild=True)
                self.connect(thread, QtCore.SIGNAL("exception"), 
                             lambda exc_info: show_exc_info(self._gui, exc_info[1], details=format_exc_info(*exc_info)))
                self.connect(thread, QtCore.SIGNAL("progress"), 
                             lambda percents, row: refresh(percents, row))
                self.connect(thread, QtCore.SIGNAL("finished"), 
                             lambda: self._gui.showMessageOnStatusBar(self.tr("Rebuild thumbnails is done.")))
                thread.start()
                    
            finally:
                uow.close()
            
        except Exception as ex:
            show_exc_info(self._gui, ex)
            
class DeleteItemActionHandler(AbstractActionHandler):
    def __init__(self, gui):
        super(DeleteItemActionHandler, self).__init__(gui)
    
    def handle(self):
        try:
            self._gui.checkActiveRepoIsNotNone()
            self._gui.checkActiveUserIsNotNone()
                        
            itemIds = self._gui.selectedItemIds()
            if len(itemIds) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            mb = QtGui.QMessageBox()
            mb.setText(self.tr("Do you really want to delete {} selected file(s)?").format(len(itemIds)))
            mb.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            if mb.exec_() != QtGui.QMessageBox.Yes:
                raise CancelOperationError()
            
            thread = DeleteGroupOfItemsThread(
                self._gui, self._gui.active_repo, itemIds, self._gui.active_user.login)
                                    
            wd = WaitDialog(self._gui)
            self.connect(thread, QtCore.SIGNAL("finished"), wd.reject)
            self.connect(thread, QtCore.SIGNAL("exception"), wd.exception)
            self.connect(thread, QtCore.SIGNAL("progress"), wd.set_progress)
            wd.startWithWorkerThread(thread)
                
            if thread.errors > 0:
                mb = MyMessageBox(self._gui)
                mb.setWindowTitle(self.tr("Information"))
                mb.setText(self.tr("There were {0} errors.").format(thread.errors))                    
                mb.setDetailedText(thread.detailed_message)
                mb.exec_()
                
        except CancelOperationError:
            self._gui.showMessageOnStatusBar(self.tr("Operation cancelled."), STATUSBAR_TIMEOUT)
            
        except Exception as ex:
            show_exc_info(self._gui, ex)
            
        else:
            #TODO: display information about how many items were deleted
            self._gui.showMessageOnStatusBar(self.tr("Operation completed."), STATUSBAR_TIMEOUT)
            self.emit(QtCore.SIGNAL("handlerSignal"), HandlerSignals.ITEM_DELETED)
            

class OpenItemActionHandler(AbstractActionHandler):
    def __init__(self, gui):
        super(OpenItemActionHandler, self).__init__(gui)
    
    def handle(self):
        try:
            sel_rows = self._gui.selectedRows()
            if len(sel_rows) != 1:
                raise MsgException(self.tr("Select one item, please."))
            
            data_ref = self._gui.itemAtRow(sel_rows.pop()).data_ref
            
            if not data_ref or data_ref.type != DataRef.FILE:
                raise MsgException(self.tr("Action 'View item' can be applied only to items linked with files."))
            
            eam = ExtAppMgr()
            eam.invoke(os.path.join(self._gui.active_repo.base_path, data_ref.url))
            
        except Exception as ex:
            show_exc_info(self._gui, ex)
        else:
            self._gui.showMessageOnStatusBar(self.tr("Operation completed."), STATUSBAR_TIMEOUT)    
    
class OpenItemWithInternalImageViewerActionHandler(AbstractActionHandler):
    def __init__(self, gui):
        super(OpenItemWithInternalImageViewerActionHandler, self).__init__(gui)
        
    def handle(self):
        try:
            self._gui.checkActiveRepoIsNotNone()
            self._gui.checkActiveUserIsNotNone()            
            
            rows = self._gui.selectedRows()
            if len(rows) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            start_index = 0
            abs_paths = []
            if len(rows) == 1:
                #If there is only one selected item, pass to viewer all items in this table model
                for row in range(self._gui.rowCount()):
                    abs_paths.append(os.path.join(
                        self._gui.active_repo.base_path, self._gui.itemAtRow(row).data_ref.url))
                #This is the index of the first image to show
                start_index = rows.pop()
            else:
                for row in rows:
                    abs_paths.append(os.path.join(
                        self._gui.active_repo.base_path, self._gui.itemAtRow(row).data_ref.url))
            
            iv = ImageViewer(self._gui.active_repo, self._gui.active_user.login, self._gui, abs_paths)
            iv.set_current_image_index(start_index)
            iv.show()
            #TODO scroll items table to the last item shown in ImageViewer
        except Exception as ex:
            show_exc_info(self._gui, ex)
        else:
            self._gui.showMessageOnStatusBar(self.tr("Operation completed."), STATUSBAR_TIMEOUT)
    
    
class ExportItemsToM3uAndOpenItActionHandler(AbstractActionHandler):
    def __init__(self, gui):
        super(ExportItemsToM3uAndOpenItActionHandler, self).__init__(gui)
        
    def handle(self):
        try:
            self._gui.checkActiveRepoIsNotNone()
            self._gui.checkActiveUserIsNotNone()
            
            rows = self._gui.selectedRows()
            if len(rows) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            tmp_dir = UserConfig().get("tmp_dir", consts.DEFAULT_TMP_DIR)
            if not os.path.exists(tmp_dir):
                os.makedirs(tmp_dir)
            m3u_filename = str(os.getpid()) + self._gui.active_user.login + str(time.time()) + ".m3u"
            m3u_file = open(os.path.join(tmp_dir, m3u_filename), "wt")
            for row in rows:
                m3u_file.write(os.path.join(self._gui.active_repo.base_path, 
                                            self._gui.itemAtRow(row).data_ref.url) + os.linesep)                                            
            m3u_file.close()
            
            eam = ExtAppMgr()
            eam.invoke(os.path.join(tmp_dir, m3u_filename))
            
        except Exception as ex:
            show_exc_info(self._gui, ex)
        else:
            self._gui.showMessageOnStatusBar(self.tr("Operation completed."), STATUSBAR_TIMEOUT)

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
            eam.external_file_manager(os.path.join(self._gui.active_repo.base_path, data_ref.url))
                        
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
            self._gui.checkActiveRepoIsNotNone()
            
            itemIds = self._gui.selectedItemIds()
            if len(itemIds) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            exportFilename = QtGui.QFileDialog.getSaveFileName(
                parent=self._gui, caption=self.tr('Save data as..')) 
            if not exportFilename:
                raise MsgException(self.tr("You haven't chosen a file. Operation canceled."))
            
            thread = ExportItemsThread(self._gui, self._gui.active_repo, itemIds, exportFilename)
                                    
            wd = WaitDialog(self._gui)
            self.connect(thread, QtCore.SIGNAL("progress"), wd.set_progress)
            self.connect(thread, QtCore.SIGNAL("finished"), wd.reject)
            self.connect(thread, QtCore.SIGNAL("exception"), wd.exception)
            wd.startWithWorkerThread(thread)
            

        except Exception as ex:
            show_exc_info(self._gui, ex)
        else:
            #TODO: display information about how many items were exported
            self._gui.showMessageOnStatusBar(self.tr("Operation completed."), STATUSBAR_TIMEOUT)

class ImportItemsActionHandler(AbstractActionHandler):
    ''' Imports previously exported items.
    '''
    def __init__(self, gui):
        super(ImportItemsActionHandler, self).__init__(gui)
    
    def handle(self):
        try:
            self._gui.checkActiveRepoIsNotNone()
            self._gui.checkActiveUserIsNotNone()
            
            importFromFilename = QtGui.QFileDialog.getOpenFileName(
                parent=self._gui, caption=self.tr('Open reggata export file..')) 
            if not importFromFilename:
                raise MsgException(self.tr("You haven't chosen a file. Operation canceled."))
            
            thread = ImportItemsThread(self._gui, self._gui.active_repo, importFromFilename, 
                                       self._gui.active_user.login)
                                    
            wd = WaitDialog(self._gui)
            self.connect(thread, QtCore.SIGNAL("progress"), wd.set_progress)
            self.connect(thread, QtCore.SIGNAL("finished"), wd.reject)
            self.connect(thread, QtCore.SIGNAL("exception"), wd.exception)
            wd.startWithWorkerThread(thread)

        except Exception as ex:
            show_exc_info(self._gui, ex)
        else:
            self.emit(QtCore.SIGNAL("handlerSignal"), HandlerSignals.ITEM_CREATED)
            #TODO: display information about how many items were imported
            self._gui.showMessageOnStatusBar(self.tr("Operation completed."), STATUSBAR_TIMEOUT)
            
        

class ExportItemsFilesActionHandler(AbstractActionHandler):
    def __init__(self, gui):
        super(ExportItemsFilesActionHandler, self).__init__(gui)
        
    def handle(self):
        try:
            self._gui.checkActiveRepoIsNotNone()
            
            item_ids = self._gui.selectedItemIds()
            if len(item_ids) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            export_dir_path = QtGui.QFileDialog.getExistingDirectory(
                self._gui, self.tr("Choose a directory path to export files into."))
            if not export_dir_path:
                raise MsgException(self.tr("You haven't chosen existent directory. Operation canceled."))
            
            thread = ExportItemsFilesThread(self._gui, self._gui.active_repo, item_ids, export_dir_path)
                                    
            wd = WaitDialog(self._gui)
            self.connect(thread, QtCore.SIGNAL("progress"), wd.set_progress)
            self.connect(thread, QtCore.SIGNAL("finished"), wd.reject)
            self.connect(thread, QtCore.SIGNAL("exception"), wd.exception)
            wd.startWithWorkerThread(thread)
            

        except Exception as ex:
            show_exc_info(self._gui, ex)
        else:
            #TODO: display information about how many files were copied
            self._gui.showMessageOnStatusBar(self.tr("Operation completed."), STATUSBAR_TIMEOUT)

class ExportItemsFilePathsActionHandler(AbstractActionHandler):
    def __init__(self, gui):
        super(ExportItemsFilePathsActionHandler, self).__init__(gui)
        
    def handle(self):
        try:
            self._gui.checkActiveRepoIsNotNone()
            
            rows = self._gui.selectedRows()
            if len(rows) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            export_filename = QtGui.QFileDialog.getSaveFileName(
                parent=self._gui, caption=self.tr('Save results in a file.')) 
            if not export_filename:
                raise MsgException(self.tr("Operation canceled."))
            
            file = open(export_filename, "w", newline='')
            for row in rows:
                item = self._gui.itemAtRow(row)
                if item.is_data_ref_null():
                    continue
                textline = self._gui.active_repo.base_path + \
                    os.sep + self._gui.itemAtRow(row).data_ref.url + os.linesep
                file.write(textline)
            file.close()

        except Exception as ex:
            show_exc_info(self._gui, ex)
        else:
            self._gui.showMessageOnStatusBar(self.tr("Operation completed."), STATUSBAR_TIMEOUT)


class FixItemIntegrityErrorActionHandler(AbstractActionHandler):
    def __init__(self, gui, strategy):
        super(FixItemIntegrityErrorActionHandler, self).__init__(gui)
        self.__strategy = strategy
    
    def handle(self):
        
        def refresh(percent, row):
            self._gui.showMessageOnStatusBar(self.tr("Integrity fix {0}%").format(percent))
            
            #TODO: Have to replace this direct updates with emitting some specific signals..
            self._gui.resetSingleRow(row)
            QtCore.QCoreApplication.processEvents()
        
        try:
            self._gui.checkActiveRepoIsNotNone()
            self._gui.checkActiveUserIsNotNone()
            
            rows = self._gui.selectedRows()
            if len(rows) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            items = []
            for row in rows:
                item = self._gui.itemAtRow(row) 
                item.table_row = row
                items.append(item)
                        
            thread = ItemIntegrityFixerThread(
                self._gui, self._gui.active_repo, items, self._gui.items_lock, self.__strategy, self._gui.active_user.login)
            
            self.connect(thread, QtCore.SIGNAL("progress"),
                         lambda percents, row: refresh(percents, row))
            self.connect(thread, QtCore.SIGNAL("finished"),
                         lambda: self._gui.showMessageOnStatusBar(self.tr("Integrity fixing is done.")))
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
            self._gui.showMessageOnStatusBar(self.tr("Integrity check {0}%").format(percent))            
            
            #TODO: Have to replace this direct updates with emitting some specific signals..
            self._gui.resetSingleRow(row)
            QtCore.QCoreApplication.processEvents()
        
        try:
            self._gui.checkActiveRepoIsNotNone()
            self._gui.checkActiveUserIsNotNone()            
            
            rows = self._gui.selectedRows()
            if len(rows) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            items = []
            for row in rows:
                item = self._gui.itemAtRow(row)
                item.table_row = row
                items.append(item)
             
            thread = ItemIntegrityCheckerThread(
                self._gui, self._gui.active_repo, items, self._gui.items_lock)
            self.connect(thread, QtCore.SIGNAL("progress"), 
                         lambda percents, row: refresh(percents, row))
            self.connect(thread, QtCore.SIGNAL("finished"), 
                         lambda error_count: self._gui.showMessageOnStatusBar(self.tr("Integrity check is done. {0} Items with errors.").format(error_count)))            
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
            self._gui.showMessageOnStatusBar(self.tr("Operation completed."), STATUSBAR_TIMEOUT)
    
    
    
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

    
