'''
Created on 23.12.2012
@author: vlkv
'''
from reggata.logic.handler_signals import HandlerSignals
import reggata.consts as consts
from reggata.data.commands import *
from reggata.logic.action_handlers import AbstractActionHandler
from reggata.gui.item_dialog import ItemDialog
from reggata.logic.worker_threads import UpdateGroupOfItemsThread, BackgrThread, CreateGroupOfItemsThread
from reggata.gui.items_dialog import ItemsDialog


class AddItemAlgorithms(object):
    
    @staticmethod
    def addItems(tool, dialogs, listOfPaths):
        '''
            Creates and saves in repository a number of items linked with files defined by given listOfPaths.
        listOfPaths is a list of paths to files and directories. Depending on the elements of 
        listOfPaths one or another add algorithm is chosen.
            Returns a tuple (itemsCreatedCount, filesSkippedCount, listOfSavedItemIds) or raises 
        an exception.
        '''
        itemsCreatedCount = 0
        filesSkippedCount = 0
        lastSavedItemIds = []
        
        if len(listOfPaths) == 0:
            # User wants to add a single Item without any file
            savedItemId = AddItemAlgorithms.addSingleItem(tool, dialogs)
            itemsCreatedCount += 1
            lastSavedItemIds.append(savedItemId)
            
        elif len(listOfPaths) == 1 :
            file = listOfPaths[0]
            if os.path.isdir(file):
                # User wants to create Items for all files in selected directory
                (itemsCreatedCount, filesSkippedCount, savedItemIds) = \
                    AddItemAlgorithms.addManyItemsRecursively(tool, dialogs, [file])
                itemsCreatedCount += itemsCreatedCount
                filesSkippedCount += filesSkippedCount
                lastSavedItemIds.extend(savedItemIds)
            else:
                # User wants to add single Item with file
                savedItemId = AddItemAlgorithms.addSingleItem(tool, dialogs, file)
                itemsCreatedCount += 1
                lastSavedItemIds.append(savedItemId)
        else:
            # User wants to create Items for a whole list of files and dirs
            (itemsCreatedCount, filesSkippedCount, savedItemIds) = \
                AddItemAlgorithms.addManyItemsRecursively(tool, dialogs, listOfPaths)
            itemsCreatedCount += itemsCreatedCount
            filesSkippedCount += filesSkippedCount
            lastSavedItemIds.extend(savedItemIds)
        return (itemsCreatedCount, filesSkippedCount, lastSavedItemIds)
    
    
    @staticmethod
    def addSingleItem(tool, dialogs, file=None):
        '''
            Creates and saves in repo an Item linked with a given file (or without file). 
        Returns id of saved Item, or raises an exception.
        '''
        savedItemId = None

        item = Item(user_login=tool.user.login)
        if not helpers.is_none_or_empty(file):
            file = os.path.normpath(file)
            item.title, _ = os.path.splitext(os.path.basename(file))
            item.data_ref = DataRef(type=DataRef.FILE, url=file)

        if not dialogs.execItemDialog(
            item=item, gui=tool.gui, repo=tool.repo, dialogMode=ItemDialog.CREATE_MODE):
            raise CancelOperationError("User cancelled operation.")
        
        uow = tool.repo.createUnitOfWork()
        try:
            srcAbsPath = None
            dstRelPath = None
            if item.data_ref is not None:
                srcAbsPath = item.data_ref.srcAbsPath
                dstRelPath = item.data_ref.dstRelPath

            cmd = SaveNewItemCommand(item, srcAbsPath, dstRelPath)
            thread = BackgrThread(tool.gui, uow.executeCommand, cmd)
            
            dialogs.startThreadWithWaitDialog(
                thread, tool.gui, indeterminate=True)
            
            savedItemId = thread.result
            
        finally:
            uow.close()
            
        return savedItemId
    
    @staticmethod
    def addManyItems(tool, dialogs, files):
        '''
            Creates and saves in repository items linked with given list of files (filenames). 
        Returns a tuple (itemsCreatedCount, filesSkippedCount, listOfSavedItemIds) or raises an
        exception.
        '''
        if len(files) <= 1:
            raise ValueError("You should give more than one file.")
        
        items = []
        for file in files:
            file = os.path.normpath(file)
            item = Item(user_login=tool.user.login)
            item.title, _ = os.path.splitext(os.path.basename(file))
            item.data_ref = DataRef(type=DataRef.FILE, url=file) #DataRef.url can be changed in ItemsDialog
            item.data_ref.srcAbsPath = file
            items.append(item)
        
        if not dialogs.execItemsDialog(
            items, tool.gui, tool.repo, ItemsDialog.CREATE_MODE, sameDstPath=True):
            raise CancelOperationError("User cancelled operation.")
        
        thread = CreateGroupOfItemsThread(tool.gui, tool.repo, items)
        
        dialogs.startThreadWithWaitDialog(
                thread, tool.gui, indeterminate=False)
            
        return (thread.createdCount, thread.skippedCount, thread.lastSavedItemIds)


    @staticmethod
    def addManyItemsRecursively(tool, dialogs, listOfPaths):
        '''
            Creates and saves in repository a number of items linked with files defined by given listOfPaths.
        listOfPaths is a list of paths to files and directories. For every file an Item is created. 
        Every directory is scanned recursively and for every file found an Item is created.
        Returns a tuple (itemsCreatedCount, filesSkippedCount, listOfSavedItemIds) or raises 
        an exception.
        '''
        items = []
        for path in listOfPaths:
            path = os.path.normpath(path)
            
            if os.path.isfile(path):
                file = path
                item = Item(user_login=tool.user.login)
                item.title, _ = os.path.splitext(file)
                srcAbsPath = os.path.abspath(file)
                item.data_ref = DataRef(type=DataRef.FILE, url=srcAbsPath) #DataRef.url can be changed in ItemsDialog
                item.data_ref.srcAbsPath = srcAbsPath
                item.data_ref.srcAbsPathToRoot = os.path.dirname(file)
                # item.data_ref.dstRelPath will be set by ItemsDialog
                items.append(item)
            elif os.path.isdir(path):
                dirPath = path
                for root, dirs, files in os.walk(dirPath):
                    if os.path.relpath(root, dirPath) == ".reggata":
                        continue
                    for file in files:
                        item = Item(user_login=tool.user.login)
                        item.title, _ = os.path.splitext(file)
                        srcAbsPath = os.path.join(root, file)
                        item.data_ref = DataRef(type=DataRef.FILE, url=srcAbsPath) #DataRef.url can be changed in ItemsDialog
                        item.data_ref.srcAbsPath = srcAbsPath
                        item.data_ref.srcAbsPathToRoot = os.path.join(dirPath, "..")
                        # item.data_ref.dstRelPath will be set by ItemsDialog
                        items.append(item)
            else:
                logger.info("Skipping path '{}'".format(path))
        
        if not dialogs.execItemsDialog(
            items, tool.gui, tool.repo, ItemsDialog.CREATE_MODE, sameDstPath=False):
            raise CancelOperationError("User cancelled operation.")
            
        thread = CreateGroupOfItemsThread(tool.gui, tool.repo, items)
        
        dialogs.startThreadWithWaitDialog(
                thread, tool.gui, indeterminate=False)
            
        return (thread.createdCount, thread.skippedCount, thread.lastSavedItemIds)
        


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
