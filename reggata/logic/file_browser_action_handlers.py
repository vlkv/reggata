'''
Created on 23.12.2012
@author: vlkv
'''
from reggata.logic.action_handlers import AbstractActionHandler
import reggata.errors as err
import reggata.consts as consts
from reggata.logic.handler_signals import HandlerSignals
from reggata.logic.common_action_handlers import AddItemAlgorithms
from reggata.helpers import show_exc_info
import os



class AddFileToRepoActionHandler(AbstractActionHandler):
    def __init__(self, tool, dialogs):
        super(AddFileToRepoActionHandler, self).__init__(tool)
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

