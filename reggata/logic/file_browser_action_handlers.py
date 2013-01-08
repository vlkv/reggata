'''
Created on 23.12.2012
@author: vlkv
'''
import os
from reggata.logic.action_handlers import AbstractActionHandler
from reggata.errors import MsgException, CancelOperationError
import reggata.helpers as helpers
from reggata.logic.handler_signals import HandlerSignals
import reggata.consts as consts
from reggata.gui.drop_files_dialogs_facade import DropFilesDialogsFacade
from reggata.data.commands import GetFileInfoCommand, FileInfo
from reggata.logic.common_action_handlers import AddItemAlgorithms
from reggata.helpers import show_exc_info


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
                raise MsgException(self.tr("There are no selected files."))

            (self._itemsCreatedCount, self._filesSkippedCount, self.lastSavedItemIds) = \
                AddItemAlgorithms.addItems(self._tool, self._dialogs, files)

            self._emitHandlerSignal(HandlerSignals.ITEM_CREATED)

        except CancelOperationError:
            return
        except Exception as ex:
            show_exc_info(self._tool.gui, ex)
        finally:
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE,
                self.tr("Operation completed. Added {}, skipped {} files.")
                    .format(self._itemsCreatedCount, self._filesSkippedCount))
