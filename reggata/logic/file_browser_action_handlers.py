'''
Created on 23.12.2012
@author: vlkv
'''
import os
from reggata.logic.action_handlers import AbstractActionHandler
from reggata.errors import MsgException
import reggata.helpers as helpers
from reggata.logic.handler_signals import HandlerSignals
import reggata.consts as consts
from reggata.gui.drop_files_dialogs_facade import DropFilesDialogsFacade
from reggata.logic.items_table_action_handlers import AddSingleItemActionHandler
from reggata.data.commands import GetFileInfoCommand, FileInfo


class AddFileToRepoActionHandler(AbstractActionHandler):
    def __init__(self, tool, dialogs):
        super(AddFileToRepoActionHandler, self).__init__(tool)
        self._dialogs = dialogs
        
    def handle(self):
        try:
            self._tool.checkActiveRepoIsNotNone()
            self._tool.checkActiveUserIsNotNone()
            
            files = self._tool.gui.selectedFiles()
            if len(files) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            if len(files) > 1:
                raise MsgException(self.tr("Select one file please."))
            
            finfo = None
            uow = self._tool.repo.createUnitOfWork()
            try:
                cmd = GetFileInfoCommand(os.path.relpath(files[0], self._tool.repo.base_path))
                finfo = uow.executeCommand(cmd)
            finally:
                uow.close()
            
            if finfo is None or len(finfo.itemIds) > 0:
                raise MsgException("Cannot add given file to the repo.")
                
            
            
            dialogs = DropFilesDialogsFacade(self._dialogs)
            dialogs.setSelectedFiles(files)
            secondHandler = AddSingleItemActionHandler(self._tool, dialogs)
            secondHandler.handle()
        
            self._emitHandlerSignal(HandlerSignals.STATUS_BAR_MESSAGE, 
                                    self.tr("Added one file to the repo."), consts.STATUSBAR_TIMEOUT)
            self._emitHandlerSignal(HandlerSignals.ITEM_CREATED)
                            
        except Exception as ex:
            helpers.show_exc_info(self._tool.gui, ex)
            
        
        

