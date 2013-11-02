'''
Created on 01.10.2012
@author: vlkv
'''
import os
import time
from PyQt4 import QtCore, QtGui
import reggata.consts as consts
import reggata.errors as errors
import reggata.data.db_schema as db
import reggata.statistics as stats
import reggata.logic.worker_threads as threads
from reggata.logic.action_handlers import AbstractActionHandler
from reggata.logic.common_action_handlers import AddItemAlgorithms
from reggata.logic.common_action_handlers import EditItemsActionHandler
from reggata.logic.handler_signals import HandlerSignals
from reggata.user_config import UserConfig
from reggata.helpers import show_exc_info, format_exc_info
from reggata.gui.image_viewer import ImageViewer



class AddItemsActionHandler(AbstractActionHandler):
    def __init__(self, tool, dialogs):
        super(AddItemsActionHandler, self).__init__(tool)
        self.__dialogs = dialogs
        self._itemsCreatedCount = 0
        self._filesSkippedCount = 0
        self.lastSavedItemIds = []

    def handle(self):
        try:
            self._tool.checkActiveRepoIsNotNone()
            self._tool.checkActiveUserIsNotNone()

            files = self.__dialogs.getOpenFilesAndDirs(
                self._tool.gui, self.tr("Select files you want to add to the repository"))

            # NOTE: if len(files) == 0 (user haven't selected any files) then it is supposed that
            # an Item without file should be created.

            (self._itemsCreatedCount, self._filesSkippedCount, self.lastSavedItemIds) = \
                AddItemAlgorithms.addItems(self._tool, self.__dialogs, files)

            self._emitHandlerSignal(HandlerSignals.ITEM_CREATED)

            stats.sendEvent("items_table.add_items")

        except errors.CancelOperationError:
            return
        except Exception as ex:
            show_exc_info(self._tool.gui, ex)
        finally:
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Operation completed. Added {}, skipped {} files.")
                    .format(self._itemsCreatedCount, self._filesSkippedCount))


class EditItemsActionHandlerItemsTable(EditItemsActionHandler):
    def __init__(self, tool, dialogs):
        super(EditItemsActionHandlerItemsTable, self).__init__(tool, dialogs)

    def handle(self):
        super(EditItemsActionHandlerItemsTable, self).handle()
        stats.sendEvent("items_table.edit_items")




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
                raise errors.MsgException(self.tr("There are no selected items."))


            uow = self._tool.repo.createUnitOfWork()
            try:
                items = []
                for row in rows:
                    item = self._tool.gui.itemAtRow(row)
                    item.table_row = row
                    items.append(item)

                thread = threads.ThumbnailBuilderThread(
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

            stats.sendEvent("items_table.rebuild_item_thumbnail")

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
                raise errors.MsgException(self.tr("There are no selected items."))

            mbResult = self._dialogs.execMessageBox(self._tool.gui,
                text=self.tr("Do you really want to delete {} selected file(s)?").format(len(itemIds)),
                buttons=[QtGui.QMessageBox.Yes, QtGui.QMessageBox.No])
            if mbResult != QtGui.QMessageBox.Yes:
                raise errors.CancelOperationError()

            thread = threads.DeleteGroupOfItemsThread(
                self._tool.gui, self._tool.repo, itemIds, self._tool.user.login)

            self._dialogs.startThreadWithWaitDialog(thread, self._tool.gui, indeterminate=False)

            if thread.errors > 0:
                self._dialogs.execMessageBox(self._tool.gui,
                    text=self.tr("There were {0} errors.").format(thread.errors),
                    detailedText=thread.detailed_message)

            stats.sendEvent("items_table.delete_item")

        except errors.CancelOperationError:
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
                raise errors.MsgException(self.tr("Select one item, please."))

            dataRef = self._tool.gui.itemAtRow(selRows.pop()).data_ref

            if dataRef is None or dataRef.type != db.DataRef.FILE:
                raise errors.MsgException(self.tr("This action can be applied only to the items linked with files."))

            self._extAppMgr.openFileWithExtApp(os.path.join(self._tool.repo.base_path, dataRef.url))

            stats.sendEvent("items_table.open_item")

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
                raise errors.MsgException(self.tr("There are no selected items."))

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

            stats.sendEvent("items_table.open_item_with_internal_image_viewer")

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
                raise errors.MsgException(self.tr("There are no selected items."))

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

            stats.sendEvent("items_table.export_items_to_m3u_and_open_it")

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
                raise errors.MsgException(self.tr("Select one item, please."))

            dataRef = self._tool.gui.itemAtRow(selRows.pop()).data_ref

            if dataRef is None or dataRef.type != db.DataRef.FILE:
                raise errors.MsgException(
                    self.tr("This action can be applied only to the items linked with files."))


            self._extAppMgr.openContainingDirWithExtAppManager(
                os.path.join(self._tool.repo.base_path, dataRef.url))

            stats.sendEvent("items_table.open_item_with_ext_file_manager")

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
                raise errors.MsgException(self.tr("There are no selected items."))

            exportFilename = self._dialogs.getSaveFileName(
                self._tool.gui,
                self.tr('Save data as..'),
                self.tr("Reggata Archive File (*.raf)"))
            if not exportFilename:
                raise errors.MsgException(self.tr("You haven't chosen a file. Operation canceled."))

            if not exportFilename.endswith(".raf"):
                exportFilename += ".raf"

            if os.path.exists(exportFilename):
                mbRes = self._dialogs.execMessageBox(self._tool.gui,
                                             text=self.tr("File {} already exists. Do you want to overwrite it?")
                                             .format(exportFilename),
                                             buttons=[QtGui.QMessageBox.Yes | QtGui.QMessageBox.No])
                if mbRes != QtGui.QMessageBox.Yes:
                    return

            thread = threads.ExportItemsThread(self, self._tool.repo, itemIds, exportFilename)

            self._dialogs.startThreadWithWaitDialog(thread, self._tool.gui, indeterminate=False)

            self._exported = thread.exportedCount
            self._skipped = thread.skippedCount

            stats.sendEvent("items_table.export_items")

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
                raise errors.MsgException(self.tr("There are no selected items."))

            dstDirPath = self._dialogs.getExistingDirectory(
                self._tool.gui, self.tr("Choose a directory path to export files into."))

            if not dstDirPath:
                raise errors.MsgException(self.tr("You haven't chosen existent directory. Operation canceled."))

            thread = threads.ExportItemsFilesThread(self, self._tool.repo, itemIds, dstDirPath)

            self._dialogs.startThreadWithWaitDialog(thread, self._tool.gui, indeterminate=False)

            self._filesExported = thread.filesExportedCount
            self._filesSkipped = thread.filesSkippedCount

            stats.sendEvent("items_table.export_items_files")

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
                raise errors.MsgException(self.tr("There are no selected items."))

            exportFilename = self._dialogs.getSaveFileName(self._tool.gui,
                self.tr('Save results in a file.'))
            if not exportFilename:
                raise errors.MsgException(self.tr("Operation canceled."))

            with open(exportFilename, "w", newline='') as exportFile:
                for row in rows:
                    item = self._tool.gui.itemAtRow(row)
                    if not item.hasDataRef():
                        continue
                    textline = self._tool.repo.base_path + \
                        os.sep + self._tool.gui.itemAtRow(row).data_ref.url + os.linesep
                    exportFile.write(textline)

            stats.sendEvent("items_table.export_items_file_paths")

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
                raise errors.MsgException(self.tr("There are no selected items."))

            items = []
            for row in rows:
                item = self._tool.gui.itemAtRow(row)
                item.table_row = row
                items.append(item)

            thread = threads.ItemIntegrityFixerThread(
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

            stats.sendEvent("items_table.fix_item_integrity_error")

        except Exception as ex:
            show_exc_info(self._tool.gui, ex)


class CheckItemIntegrityActionHandler(AbstractActionHandler):
    def __init__(self, tool):
        super(CheckItemIntegrityActionHandler, self).__init__(tool)

    def handle(self):
        def refresh(percent, topRow, bottomRow):
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Integrity check {0}%").format(percent))
            self._emitHandlerSignal(HandlerSignals.RESET_ROW_RANGE, topRow, bottomRow)
            QtCore.QCoreApplication.processEvents()

        try:
            self._tool.checkActiveRepoIsNotNone()
            self._tool.checkActiveUserIsNotNone()

            rows = self._tool.gui.selectedRows()
            if len(rows) == 0:
                raise errors.MsgException(self.tr("There are no selected items."))

            items = []
            for row in rows:
                item = self._tool.gui.itemAtRow(row)
                item.table_row = row
                items.append(item)

            thread = threads.ItemIntegrityCheckerThread(
                self._tool.gui, self._tool.repo, items, self._tool.itemsLock)

            self.connect(thread, QtCore.SIGNAL("progress"),
                         lambda percents, topRow, bottomRow: refresh(percents, topRow, bottomRow))
            self.connect(thread, QtCore.SIGNAL("finished_with_1_arg"),
                         lambda errorCount: self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                                self.tr("Integrity check is done. {} Items with errors.".format(errorCount))))
            thread.start()

            stats.sendEvent("items_table.check_item_integrity_error")

        except Exception as ex:
            show_exc_info(self._tool.gui, ex)


class OpenItemsTableSettingsDialog(AbstractActionHandler):
    def __init__(self, tool):
        super(OpenItemsTableSettingsDialog, self).__init__(tool)

    def handle(self):
        settingsGui = self._tool.createSettingsGui(self._tool.gui)
        if not settingsGui.exec_():
            return
        self._emitHandlerSignal(HandlerSignals.REGGATA_CONF_CHANGED)
