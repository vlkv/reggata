'''
Created on 23.12.2012
@author: vlkv
'''
import os
import logging
import reggata.errors as err
import reggata.consts as consts
from reggata.logic.handler_signals import HandlerSignals
from reggata.logic.action_handlers import AbstractActionHandler
from reggata.logic.common_action_handlers import AddItemAlgorithms
from reggata.helpers import show_exc_info, is_none_or_empty
import reggata.data.commands as cmds

logger = logging.getLogger(consts.ROOT_LOGGER + "." + __name__)



class AddFilesToRepoActionHandler(AbstractActionHandler):
    def __init__(self, tool, dialogs):
        super(AddFilesToRepoActionHandler, self).__init__(tool)
        self._dialogs = dialogs
        self._itemsCreatedCount = 0
        self._filesSkippedCount = 0
        self.lastSavedItemIds = []

    def handle(self):
        try:
            self._tool.checkActiveRepoIsNotNone()
            self._tool.checkActiveUserIsNotNone()

            files = self._tool.gui.selectedFiles()
            if len(files) == 0:
                raise err.MsgException(self.tr("There are no selected files."))

            (self._itemsCreatedCount, self._filesSkippedCount, self.lastSavedItemIds) = \
                AddItemAlgorithms.addItems(self._tool, self._dialogs, files)

            self._emitHandlerSignal(HandlerSignals.ITEM_CREATED)

        except err.CancelOperationError:
            return
        except Exception as ex:
            show_exc_info(self._tool.gui, ex)
        finally:
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Operation completed. Added {}, skipped {} files.")
                    .format(self._itemsCreatedCount, self._filesSkippedCount))


class OpenFileActionHandler(AbstractActionHandler):
    def __init__(self, tool, extAppMgr):
        super(OpenFileActionHandler, self).__init__(tool)
        self._extAppMgr = extAppMgr

    def handle(self):
        try:
            selFiles = self._tool.gui.selectedFiles()
            if len(selFiles) != 1:
                raise err.MsgException(self.tr("Select one file, please."))

            selFile = selFiles[0]
            assert os.path.isabs(selFiles[0]), "Path '{}' should be absolute".format(selFile)

            if os.path.isdir(selFile):
                self._extAppMgr.openContainingDirWithExtAppManager(selFile)
            elif os.path.isfile(selFile):
                self._extAppMgr.openFileWithExtApp(selFile)
            else:
                raise err.MsgException(self.tr("This is not a file and not a directory, cannot open it."))

        except Exception as ex:
            show_exc_info(self._tool.gui, ex)

        else:
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Done."), consts.STATUSBAR_TIMEOUT)


class MoveFilesActionHandler(AbstractActionHandler):
    def __init__(self, tool, dialogs):
        super(MoveFilesActionHandler, self).__init__(tool)
        self._dialogs = dialogs

    def handle(self):
        logger.info("MoveFilesActionHandler.handle invoked")
        try:
            self._tool.checkActiveRepoIsNotNone()
            self._tool.checkActiveUserIsNotNone()

            selFiles = self._tool.gui.selectedFiles()
            
            # TODO implement
            # Ask user to select a destination directory within repository.
            # Walk recursively in all selected dirs/files and create 
            # a list of files to move (this list would not contain any dirs).
            # Create a thread that would move files one by one showing WaitDialog to user

            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE, self.tr("Done."),
                                    consts.STATUSBAR_TIMEOUT)
            self._emitHandlerSignal(HandlerSignals.ITEM_CHANGED)
            
        except Exception as ex:
            show_exc_info(self._tool.gui, ex)


class RenameFileActionHandler(AbstractActionHandler):
    def __init__(self, tool, dialogs):
        super(RenameFileActionHandler, self).__init__(tool)
        self._dialogs = dialogs

    def handle(self):
        logger.info("RenameFileActionHandler.handle invoked")
        try:
            self._tool.checkActiveRepoIsNotNone()
            self._tool.checkActiveUserIsNotNone()

            selFiles = self._tool.gui.selectedFiles()
            if len(selFiles) != 1:
                raise err.MsgException(self.tr("Please select one file or directory"))

            selFile = selFiles[0]

            newName, isOk = self._dialogs.execGetTextDialog(
                self._tool.gui, self.tr("Rename File"), self.tr("Enter new file name:"),
                os.path.basename(selFile))

            if not isOk or newName == os.path.basename(selFile):
                return

            if is_none_or_empty(newName.strip()):
                raise err.MsgException(self.tr("Wrong input, file name cannot be empty."))

            if os.path.isdir(selFile):
                self.__renameDir(selFile, newName)
            elif os.path.isfile(selFile):
                self.__renameFile(selFile, newName)
            else:
                raise err.MsgException(self.tr(
                    "Cannot rename '{}' because it is not a file or directory."
                    .format(selFile)))

            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE, self.tr("Done."),
                                    consts.STATUSBAR_TIMEOUT)
            self._emitHandlerSignal(HandlerSignals.ITEM_CHANGED)

        except Exception as ex:
            show_exc_info(self._tool.gui, ex)

    def __renameDir(self, dirAbsPath, newDirName):
        uow = self._tool.repo.createUnitOfWork()
        try:
            uow.executeCommand(cmds.RenameDirectoryCommand(dirAbsPath, newDirName))
        finally:
            uow.close()

    def __renameFile(self, fileAbsPath, newFileName):
        uow = self._tool.repo.createUnitOfWork()
        try:
            uow.executeCommand(cmds.RenameFileCommand(fileAbsPath, newFileName))
        finally:
            uow.close()

