'''
Created on 23.12.2012
@author: vlkv
'''
from reggata.logic.handler_signals import HandlerSignals
import reggata.consts as consts
from reggata.data.commands import *
from reggata.logic.action_handlers import AbstractActionHandler
from reggata.gui.item_dialog import ItemDialog
from reggata.logic.worker_threads import UpdateGroupOfItemsThread
from reggata.gui.items_dialog import ItemsDialog



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
