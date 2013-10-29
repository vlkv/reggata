'''
Created on 19.12.2012
@author: vlkv
'''
import logging
import os
from PyQt4 import QtCore
import traceback
from datetime import datetime
from reggata.logic.abstract_tool import AbstractTool
from reggata.gui.file_browser_gui import FileBrowserGui
from reggata.errors import NoneError
from reggata.errors import NotExistError
from reggata.errors import CurrentRepoIsNoneError
from reggata.errors import CurrentUserIsNoneError
import reggata.helpers as helpers
from reggata.data.commands import FileInfo
from reggata.data.commands import GetFileInfoCommand
from reggata.data.commands import GetItemIdsWithFilesFrom
from reggata.logic.action_handlers import ActionHandlerStorage
from reggata.logic.handler_signals import HandlerSignals
from reggata.gui.drop_files_dialogs_facade import DropFilesDialogsFacade
from reggata.logic.file_browser_action_handlers import AddFilesToRepoActionHandler
from reggata.logic.file_browser_action_handlers import OpenFileActionHandler
from reggata.logic.file_browser_action_handlers import MoveFilesActionHandler
from reggata.logic.file_browser_action_handlers import RenameFileActionHandler
from reggata.logic.file_browser_action_handlers import DeleteFilesActionHandler
from reggata.logic.file_browser_action_handlers import EditItemsActionHandlerFileBrowser
from reggata.logic.ext_app_mgr import ExtAppMgr

logger = logging.getLogger(__name__)


class FileBrowser(AbstractTool):

    TOOL_ID = "FileBrowserTool"

    def __init__(self, guiUpdater, dialogsFacade):
        super(FileBrowser, self).__init__()
        self._guiUpdater = guiUpdater
        self._actionHandlers = None
        self._dialogsFacade = dialogsFacade
        self.__dropFilesDialogs = DropFilesDialogsFacade(dialogsFacade)
        self._gui = None
        self._repo = None
        self._user = None
        self._currDir = None
        self._listCache = None
        self._mutex = None
        self._thread = None
        self._enabled = False
        self._extAppMgr = ExtAppMgr()

        self._guiUpdater.subscribe(
            self._extAppMgr, self._extAppMgr.updateState,
            [HandlerSignals.REGGATA_CONF_CHANGED])

        logger.debug("File Browser __init__ finished.")


    def id(self):
        return self.TOOL_ID

    def title(self):
        return self.tr("File Browser")

    def createGui(self, guiParent):
        self._gui = FileBrowserGui(guiParent, self)
        self._actionHandlers = ActionHandlerStorage(self._guiUpdater)
        logger.debug("File Browser GUI created.")
        return self._gui

    def __getGui(self):
        return self._gui
    gui = property(fget=__getGui)


    def connectActionsWithActionHandlers(self):
        assert len(self._gui.actions) > 0, "Actions should be already built in ToolGui"

        self._actionHandlers.register(
            self._gui.actions['editItems'],
            EditItemsActionHandlerFileBrowser(self, self._dialogsFacade))

        self._actionHandlers.register(
            self._gui.actions['addFiles'],
            AddFilesToRepoActionHandler(self, self._dialogsFacade))

        self._actionHandlers.register(
            self._gui.actions['openFile'],
            OpenFileActionHandler(self, self._extAppMgr))

        self._actionHandlers.register(
            self._gui.actions['moveFiles'],
            MoveFilesActionHandler(self, self._dialogsFacade))

        self._actionHandlers.register(
            self._gui.actions['renameFile'],
            RenameFileActionHandler(self, self._dialogsFacade))

        self._actionHandlers.register(
            self._gui.actions['deleteFiles'],
            DeleteFilesActionHandler(self, self._dialogsFacade))




    def handlerSignals(self):
        return [([HandlerSignals.ITEM_CHANGED,
                  HandlerSignals.ITEM_CREATED,
                  HandlerSignals.ITEM_DELETED], self.refreshDir)]


    @property
    def repo(self):
        return self._repo

    def setRepo(self, repo):
        self._repo = repo
        if repo is not None:
            self.changeDir(repo.base_path)
            logger.debug("File Browser curr dir has been SET.")
        else:
            self.unsetDir()
            logger.debug("File Browser curr dir has been UNSET.")

    def checkActiveRepoIsNotNone(self):
        if self._repo is None:
            raise CurrentRepoIsNoneError("Current repository is None")


    @property
    def user(self):
        return self._user

    def setUser(self, user):
        self._user = user
        # TODO: update Gui according to the user change

    def checkActiveUserIsNotNone(self):
        if self._user is None:
            raise CurrentUserIsNoneError("Current user is None")


    def enable(self):
        self._enabled = True
        self.refreshDir()
        logger.debug("File Browser enabled.")


    def disable(self):
        self._enabled = False
        logger.debug("File Browser disabled.")


    @property
    def currDir(self):
        if self._currDir is None:
            raise NoneError()
        return self._currDir


    def repoBasePath(self):
        if self._repo is None:
            raise NoneError()
        return self._repo.base_path


    def itemIdsForDir(self, dirAbsPath):
        assert self._repo is not None
        dirRelPath = os.path.relpath(dirAbsPath, self._repo.base_path)
        itemIds = []
        try:
            uow = self._repo.createUnitOfWork()
            cmd = GetItemIdsWithFilesFrom(dirRelPath)
            itemIds = uow.executeCommand(cmd)
        finally:
            uow.close()
        return itemIds



    def listDir(self):
        if self._currDir is None:
            return []
        if self._listCache is None:
            self._rebuildListCache()
        return self._listCache


    def filesCount(self):
        if self._currDir is None:
            return 0
        if self._listCache is None:
            self._rebuildListCache()
        return len(self._listCache)


    def _rebuildListCache(self):
        if not self._enabled:
            self._listCache = []
            return

        def resetGuiTableRows(topRow, bottomRow):
            self._gui.resetTableRows(topRow, bottomRow)
            QtCore.QCoreApplication.processEvents()

        assert self._currDir is not None
        resultDirs = [FileInfo("..", FileInfo.DIR)]
        resultFiles = []
        for fname in os.listdir(self._currDir):
            absPath = os.path.join(self._currDir, fname)
            if os.path.isfile(absPath):
                resultFiles.append(FileInfo(absPath, FileInfo.FILE))
            elif os.path.isdir(absPath):
                resultDirs.append(FileInfo(absPath, FileInfo.DIR))
        self._listCache = resultDirs + resultFiles

        logger.debug("_rebuildListCache is about to start the FileInfoSearcherThread")
        self._thread = FileInfoSearcherThread(self, self._repo, self._listCache, self._mutex)
        self.connect(self._thread, QtCore.SIGNAL("progress"),
                         lambda topRow, bottomRow: resetGuiTableRows(topRow, bottomRow))
        self._thread.start()
        #self._thread.run()


    def changeDirUp(self):
        self.changeDir("..")


    def changeRelDir(self, relativeDir):
        absDir = os.path.join(self._currDir, relativeDir)
        absDir = os.path.normpath(absDir)
        self.changeDir(absDir)


    def refreshDir(self):
        if self._currDir is None:
            return
        self.changeDir(self._currDir)


    def changeDir(self, directory):
        if directory == ".":
            directory = self._currDir

        if directory == "..":
            directory, _ = os.path.split(self._currDir)

        if not os.path.exists(directory):
            raise NotExistError(directory + " not exists on the file system.")

        if not helpers.is_internal(directory, self.repoBasePath()):
            raise ValueError(directory +  " is outside the repository.")

        if os.path.isfile(directory):
            raise ValueError(directory + " is not a directory but a file.")

        assert os.path.isabs(directory)
        self.__setCurrDir(directory)


    def unsetDir(self):
        self.__setCurrDir(None)


    def __setCurrDir(self, directory):
        if self._thread is not None:
            self._thread.interrupt = True
            self._thread.wait()
        self._currDir = directory
        self._listCache = None
        self._mutex = QtCore.QMutex()
        self._gui.resetTableModel(self._mutex)

    def storeCurrentState(self):
        self._gui.saveColumnsWidth()
        self._gui.saveColumnsVisibility()


    def restoreRecentState(self):
        self._gui.restoreColumnsVisibility()
        self._gui.restoreColumnsWidth()



class FileInfoSearcherThread(QtCore.QThread):
    def __init__(self, parent, repo, finfos, mutex):
        super(FileInfoSearcherThread, self).__init__(parent)
        self.repo = repo
        self.finfos = finfos
        self.mutex = mutex
        self.interrupt = False
        self.signalTimeoutMicroSec = 500000

    def run(self):

        logger.debug("FileInfoSearcherThread started. There are {} files to process".format(len(self.finfos)))

        uow = self.repo.createUnitOfWork()
        try:
            dtStart = None
            shouldTakeTime = True
            shouldSendProgress = False
            topRow = bottomRow = 0
            for i in range(len(self.finfos)):

                if shouldTakeTime:
                    shouldTakeTime = False
                    topRow = i
                    dtStart = datetime.now()
                if (datetime.now() - dtStart).microseconds > self.signalTimeoutMicroSec:
                    bottomRow = i
                    shouldSendProgress = True


                finfo = self.finfos[i]
                if self.interrupt:
                    logger.debug("FileInfoSearcherThread interrupted.")
                    break
                if finfo.type != FileInfo.FILE:
                    continue
                relPath = os.path.relpath(finfo.path, self.repo.base_path)
                cmd = GetFileInfoCommand(relPath)
                newFinfo = uow.executeCommand(cmd)

                self.mutex.lock()
                finfo.tags = newFinfo.tags
                finfo.fields = newFinfo.fields
                finfo.type = newFinfo.type
                finfo.status = newFinfo.status
                finfo.itemIds = newFinfo.itemIds
                self.mutex.unlock()

                if shouldSendProgress:
                    shouldSendProgress = False
                    shouldTakeTime = True
                    self.emit(QtCore.SIGNAL("progress"), topRow, bottomRow)
                    logger.debug("FileInfoSearcherThread progress: topRow={} bottomRow={}".format(topRow, bottomRow))

                # Without this sleep, GUI is not responsive... Maybe because of GIL
                self.msleep(10)

            self.emit(QtCore.SIGNAL("progress"), topRow, bottomRow)
            logger.debug("FileInfoSearcherThread last progress message: topRow={} bottomRow={}".format(topRow, bottomRow))

        except Exception as ex:
            self.emit(QtCore.SIGNAL("exception"), traceback.format_exc())
            logger.debug("FileInfoSearcherThread exception: {}".format(ex))

        finally:
            uow.close()
            self.emit(QtCore.SIGNAL("finished"))
            logger.debug("FileInfoSearcherThread done.")
