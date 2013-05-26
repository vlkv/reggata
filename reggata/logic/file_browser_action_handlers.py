'''
Created on 23.12.2012
@author: vlkv
'''
import os
import logging
import reggata.errors as err
import reggata.consts as consts
import reggata.helpers as hlp
from reggata.logic.handler_signals import HandlerSignals
from reggata.logic.action_handlers import AbstractActionHandler
from reggata.logic.common_action_handlers import AddItemAlgorithms
from reggata.logic.worker_threads import MoveFilesThread, DeleteFilesThread
from reggata.helpers import show_exc_info, is_none_or_empty
import reggata.data.commands as cmds

logger = logging.getLogger(__name__)



class AddFilesToRepoActionHandler(AbstractActionHandler):
    def __init__(self, tool, dialogs):
        super(AddFilesToRepoActionHandler, self).__init__(tool)
        self._dialogs = dialogs
        self._itemsCreatedCount = 0
        self._filesSkippedCount = 0
        self.lastSavedItemIds = []

    def handle(self):
        logger.info("AddFilesToRepoActionHandler.handle invoked")
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
        logger.info("OpenFileActionHandler.handle invoked")
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



class DeleteFilesActionHandler(AbstractActionHandler):
    def __init__(self, tool, dialogs):
        super(DeleteFilesActionHandler, self).__init__(tool)
        self._dialogs = dialogs

    def handle(self):
        logger.info("DeleteFilesActionHandler.handle invoked")
        try:
            self._tool.checkActiveRepoIsNotNone()
            self._tool.checkActiveUserIsNotNone()

            selFilesAndDirs = self._tool.gui.selectedFiles()
            selFilesAndDirs = DeleteFilesActionHandler.__filterSelectedFilesDirs(selFilesAndDirs)
            selFileAbsPaths = self.__getListOfAllAffectedFiles(selFilesAndDirs)

            thread = DeleteFilesThread(self._tool.gui, self._tool.repo, selFileAbsPaths, selFilesAndDirs)
            self._dialogs.startThreadWithWaitDialog(thread, self._tool.gui, indeterminate=False)

            if thread.errors > 0:
                self._dialogs.execMessageBox(self._tool.gui,
                                             text="There were {} errors.".format(thread.errors),
                                             detailedText=thread.detailed_message)
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE, self.tr("Done."),
                                    consts.STATUSBAR_TIMEOUT)
            self._emitHandlerSignal(HandlerSignals.ITEM_CHANGED)

        except Exception as ex:
            show_exc_info(self._tool.gui, ex)

    @staticmethod
    def __filterSelectedFilesDirs(selFiles):
        result = []
        for selFile in selFiles:
            if selFile == ".":
                continue
            elif selFile == "..":
                continue
            else:
                result.append(selFile)
        return result

    def __getListOfAllAffectedFiles(self, selFiles):
        paths = []
        for selFile in selFiles:
            if os.path.isdir(selFile):
                for root, _subdirs, files,  in os.walk(selFile):
                    for file in files:
                        fileAbsPath = os.path.join(root, file)
                        paths.append(fileAbsPath)
            elif os.path.isfile(selFile):
                paths.append(selFile)
            else:
                pass
        return paths



class MoveFilesActionHandler(AbstractActionHandler):
    def __init__(self, tool, dialogs):
        super(MoveFilesActionHandler, self).__init__(tool)
        self._dialogs = dialogs

    def handle(self):
        logger.info("MoveFilesActionHandler.handle invoked")
        try:
            self._tool.checkActiveRepoIsNotNone()
            self._tool.checkActiveUserIsNotNone()

            selFilesAndDirs = self._tool.gui.selectedFiles()
            selFilesAndDirs = MoveFilesActionHandler.__filterSelectedFilesDirs(selFilesAndDirs)
            selFileAbsPaths = self.__getListOfAllAffectedFiles(selFilesAndDirs)

            if len(selFileAbsPaths) == 0:
                return

            dstDir = self._dialogs.getExistingDirectory(self._tool.gui, self.tr("Select destination directory"))
            if not dstDir:
                return

            if not hlp.is_internal(dstDir, self._tool.repo.base_path):
                raise err.WrongValueError(self.tr("Selected directory should be within the current repo"))

            dstFileAbsPaths = []
            currDir = self._tool.currDir
            for absFile in selFileAbsPaths:
                relFile = os.path.relpath(absFile, currDir)
                dstAbsFile = os.path.join(dstDir, relFile)
                dstFileAbsPaths.append((absFile, dstAbsFile))

            thread = MoveFilesThread(self._tool.gui, self._tool.repo, dstFileAbsPaths, selFilesAndDirs)
            self._dialogs.startThreadWithWaitDialog(thread, self._tool.gui, indeterminate=False)

            if thread.errors > 0:
                self._dialogs.execMessageBox(self._tool.gui,
                                             text="There were {} errors.".format(thread.errors),
                                             detailedText=thread.detailed_message)
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE, self.tr("Done."),
                                consts.STATUSBAR_TIMEOUT)
            self._emitHandlerSignal(HandlerSignals.ITEM_CHANGED)

        except Exception as ex:
            show_exc_info(self._tool.gui, ex)



    @staticmethod
    def __filterSelectedFilesDirs(selFiles):
        result = []
        for selFile in selFiles:
            if selFile == ".":
                continue
            elif selFile == "..":
                continue
            else:
                result.append(selFile)
        return result

    def __getListOfAllAffectedFiles(self, selFiles):
        paths = []
        for selFile in selFiles:
            if os.path.isdir(selFile):
                for root, _subdirs, files,  in os.walk(selFile):
                    for file in files:
                        fileAbsPath = os.path.join(root, file)
                        paths.append(fileAbsPath)
            elif os.path.isfile(selFile):
                paths.append(selFile)
            else:
                pass
        return paths



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

