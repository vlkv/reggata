'''
Created on 01.10.2012
@author: vlkv
'''
import os
import helpers
import consts
import data.db_schema
from data.commands import *
from logic.action_handlers import AbstractActionHandler
from logic.handler_signals import HandlerSignals
from logic.worker_threads import *
from gui.item_dialog import ItemDialog
from gui.image_viewer import ImageViewer
from gui.items_dialog import ItemsDialog
from helpers import show_exc_info



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
            
            if not helpers.is_none_or_empty(file):
                file = os.path.normpath(file)
                item.title, _ = os.path.splitext(os.path.basename(file))
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
        self._skippedObjectsCount = 0
        self.lastSavedItemIds = []
    
    def _startWorkerThread(self, items):
        thread = CreateGroupOfItemsThread(self._tool.gui, self._tool.repo, items)
        
        self._dialogs.startThreadWithWaitDialog(
                thread, self._tool.gui, indeterminate=False)
            
        self._createdObjectsCount = thread.createdCount
        self._skippedObjectsCount = thread.skippedCount
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
                item.title, _ = os.path.splitext(os.path.basename(file))
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
                self.tr("Operation completed. Added {}, skipped {} files.")
                    .format(self._createdObjectsCount, self._skippedObjectsCount))
            
        
        
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
                    item = Item(user_login=self._tool.user.login)
                    item.title, _ = os.path.splitext(file)
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
                self.tr("Operation completed. Added {}, skipped {} files.")
                    .format(self._createdObjectsCount, self._skippedObjectsCount))
            



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
                                    self.tr("Editing done."), consts.STATUSBAR_TIMEOUT)
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
                self.tr("Operation cancelled."), consts.STATUSBAR_TIMEOUT)
            
        except Exception as ex:
            show_exc_info(self._tool.gui, ex)
            
        else:
            #TODO: display information about how many items were deleted
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Operation completed."), consts.STATUSBAR_TIMEOUT)
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
            
            self._extAppMgr.openFileWithExtApp(os.path.join(self._tool.repo.base_path, dataRef.url))
            
        except Exception as ex:
            show_exc_info(self._tool.gui, ex)
            
        else:
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE, 
                self.tr("Done."), consts.STATUSBAR_TIMEOUT)
    
    
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
                self.tr("Done."), consts.STATUSBAR_TIMEOUT)
            
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
                    item = self._tool.gui.itemAtRow(row)
                    if item.data_ref is None:
                        continue
                    m3uFile.write(
                        os.path.join(self._tool.repo.base_path, 
                                     item.data_ref.url) + os.linesep)                                            
                    
            self._extAppMgr.openFileWithExtApp(os.path.join(tmpDir, m3uFilename))
            
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Done."), consts.STATUSBAR_TIMEOUT)
            
        except Exception as ex:
            show_exc_info(self._tool.gui, ex)
            

class OpenItemWithExternalFileManagerActionHandler(AbstractActionHandler):
    def __init__(self, tool, extAppMgr):
        super(OpenItemWithExternalFileManagerActionHandler, self).__init__(tool)
        self._extAppMgr = extAppMgr
        
    def handle(self):
        try:
            selRows = self._tool.gui.selectedRows()
            if len(selRows) != 1:
                raise MsgException(self.tr("Select one item, please."))
            
            dataRef = self._tool.gui.itemAtRow(selRows.pop()).data_ref
            
            if dataRef is None or dataRef.type != DataRef.FILE:
                raise MsgException(
                    self.tr("This action can be applied only to the items linked with files."))
            
            
            self._extAppMgr.openContainingDirWithExtAppManager(
                os.path.join(self._tool.repo.base_path, dataRef.url))
                        
        except Exception as ex:
            show_exc_info(self._tool.gui, ex)


class ExportItemsActionHandler(AbstractActionHandler):
    '''
        Exports selected items with all their metadata (tags, fields) and
    all the referenced files. Items are packed in tar archive and later 
    they can be imported to another repository.
    '''
    def __init__(self, tool, dialogs):
        super(ExportItemsActionHandler, self).__init__(tool)
        self._dialogs = dialogs
        self._exported = 0
        self._skipped = 0
        
    def handle(self):
        try:
            self._tool.checkActiveRepoIsNotNone()
            
            itemIds = self._tool.gui.selectedItemIds()
            if len(itemIds) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            exportFilename = self._dialogs.getSaveFileName(
                self._tool.gui, 
                self.tr('Save data as..'),
                self.tr("Reggata Archive File (*.raf)"))
            if not exportFilename:
                raise MsgException(self.tr("You haven't chosen a file. Operation canceled."))
            
            thread = ExportItemsThread(self, self._tool.repo, itemIds, exportFilename)
            
            self._dialogs.startThreadWithWaitDialog(thread, self._tool.gui, indeterminate=False)
        
            self._exported = thread.exportedCount
            self._skipped = thread.skippedCount
            
        except Exception as ex:
            show_exc_info(self._tool.gui, ex)
            
        else:
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Operation completed. Exported {}, skipped {} items.")
                .format(self._exported, self._skipped))




class ExportItemsFilesActionHandler(AbstractActionHandler):
    def __init__(self, tool, dialogs):
        super(ExportItemsFilesActionHandler, self).__init__(tool)
        self._dialogs = dialogs
        self._filesExported = 0
        self._filesSkipped = 0
        
    def handle(self):
        try:
            self._tool.checkActiveRepoIsNotNone()
            
            itemIds = self._tool.gui.selectedItemIds()
            if len(itemIds) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            dstDirPath = self._dialogs.getExistingDirectory(
                self._tool.gui, self.tr("Choose a directory path to export files into."))
            
            if not dstDirPath:
                raise MsgException(self.tr("You haven't chosen existent directory. Operation canceled."))
            
            thread = ExportItemsFilesThread(self, self._tool.repo, itemIds, dstDirPath)
            
            self._dialogs.startThreadWithWaitDialog(thread, self._tool.gui, indeterminate=False)
            
            self._filesExported = thread.filesExportedCount
            self._filesSkipped = thread.filesSkippedCount
                                                
        except Exception as ex:
            show_exc_info(self._tool.gui, ex)
            
        else:
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Operation completed. Exported {}, skipped {} files."
                        .format(self._filesExported, self._filesSkipped)))


class ExportItemsFilePathsActionHandler(AbstractActionHandler):
    def __init__(self, tool, dialogs):
        super(ExportItemsFilePathsActionHandler, self).__init__(tool)
        self._dialogs = dialogs
        
    def handle(self):
        try:
            self._tool.checkActiveRepoIsNotNone()
            
            rows = self._tool.gui.selectedRows()
            if len(rows) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            exportFilename = self._dialogs.getSaveFileName(self._tool.gui, 
                self.tr('Save results in a file.'))
            if not exportFilename:
                raise MsgException(self.tr("Operation canceled."))
            
            with open(exportFilename, "w", newline='') as exportFile:
                for row in rows:
                    item = self._tool.gui.itemAtRow(row)
                    if item.is_data_ref_null():
                        continue
                    textline = self._tool.repo.base_path + \
                        os.sep + self._tool.gui.itemAtRow(row).data_ref.url + os.linesep
                    exportFile.write(textline)

        except Exception as ex:
            show_exc_info(self._tool.gui, ex)
            
        else:
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Operation completed."), consts.STATUSBAR_TIMEOUT)


class FixItemIntegrityErrorActionHandler(AbstractActionHandler):
    def __init__(self, tool, strategy):
        super(FixItemIntegrityErrorActionHandler, self).__init__(tool)
        self.__strategy = strategy
    
    def handle(self):
        
        def refresh(percent, row):
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Integrity fix {0}%").format(percent))
            self._emitHandlerSignal(HandlerSignals.RESET_SINGLE_ROW, row)
            QtCore.QCoreApplication.processEvents()
        
        try:
            self._tool.checkActiveRepoIsNotNone()
            self._tool.checkActiveUserIsNotNone()
            
            rows = self._tool.gui.selectedRows()
            if len(rows) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            items = []
            for row in rows:
                item = self._tool.gui.itemAtRow(row)
                item.table_row = row
                items.append(item)
                        
            thread = ItemIntegrityFixerThread(
                self._tool.gui, self._tool.repo, items, self._tool.itemsLock, self.__strategy, self._tool.user.login)
            
            self.connect(thread, QtCore.SIGNAL("progress"),
                         lambda percents, row: refresh(percents, row))
            self.connect(thread, QtCore.SIGNAL("finished"),
                         lambda: self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                                                         self.tr("Integrity fixing is done.")))
            self.connect(thread, QtCore.SIGNAL("exception"),
                         lambda exc_info: show_exc_info(self._tool.gui, exc_info[1], 
                                                        details=format_exc_info(*exc_info)))
            thread.start()
            
        except Exception as ex:
            show_exc_info(self._tool.gui, ex)
            

class CheckItemIntegrityActionHandler(AbstractActionHandler):
    def __init__(self, tool):
        super(CheckItemIntegrityActionHandler, self).__init__(tool)
    
    def handle(self):
        def refresh(percent, row):
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Integrity check {0}%").format(percent))
            self._emitHandlerSignal(HandlerSignals.RESET_SINGLE_ROW, row)
            QtCore.QCoreApplication.processEvents()
        
        try:
            self._tool.checkActiveRepoIsNotNone()
            self._tool.checkActiveUserIsNotNone()            
            
            rows = self._tool.gui.selectedRows()
            if len(rows) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            items = []
            for row in rows:
                item = self._tool.gui.itemAtRow(row)
                item.table_row = row
                items.append(item)
             
            thread = ItemIntegrityCheckerThread(
                self._tool.gui, self._tool.repo, items, self._tool.itemsLock)
            
            self.connect(thread, QtCore.SIGNAL("progress"), 
                         lambda percents, row: refresh(percents, row))
            self.connect(thread, QtCore.SIGNAL("finished"), 
                         lambda error_count: self._emitHandlerSignal(
                                HandlerSignals.STATUS_BAR_MESSAGE,
                                self.tr("Integrity check is done. {0} Items with errors.")
                                    .format(error_count)))
            thread.start()
            
        except Exception as ex:
            show_exc_info(self._tool.gui, ex)

