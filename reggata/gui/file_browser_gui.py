'''
Created on 19.12.2012
@author: vlkv
'''
import logging
from PyQt4 import QtCore
from PyQt4.QtCore import Qt
from reggata.gui.tool_gui import ToolGui
import reggata.consts as consts
from reggata.ui.ui_filebrowsergui import Ui_FileBrowserGui
from reggata.data.commands import FileInfo
from reggata.helpers import HTMLDelegate
import reggata.helpers as helpers

logger = logging.getLogger(consts.ROOT_LOGGER + "." + __name__)


class FileBrowserGui(ToolGui):
    
    def __init__(self, parent, fileBrowserTool):
        super(FileBrowserGui, self).__init__(parent)
        self.ui = Ui_FileBrowserGui()
        self.ui.setupUi(self)
        
        self.__fileBrowserTool = fileBrowserTool
        self.__tableModel = None
        
        self.ui.filesTableView.setItemDelegate(HTMLDelegate(self))
        self.connect(self.ui.filesTableView, QtCore.SIGNAL("activated(const QModelIndex&)"), self.__onMouseDoubleClick)
        
        self.resetTableModel(None)
        
        
    def resetTableModel(self, mutex):
        self.__tableModel = FileBrowserTableModel(self, self.__fileBrowserTool, mutex)
        self.ui.filesTableView.setModel(self.__tableModel)
        
        
    def __onMouseDoubleClick(self, index):
        filename = self.ui.filesTableView.model().data(index, FileBrowserTableModel.ROLE_FILENAME)
        try:
            self.__fileBrowserTool.changeRelDir(filename)
        except Exception as ex:
            logger.debug("Cannot change current directory: " + str(ex))

    def resetTableRow(self, row):
        self.__tableModel.resetTableRow(row)
    
    def resetTableRows(self, topRow, bottomRow):
        self.__tableModel.resetTableRows(topRow, bottomRow)
        
    def buildActions(self):
        if len(self.actions) > 0:
            logger.info("Actions already built")
            return
        
        self.actions['addFilesToRepo'] = self._createAction(self.tr("Add files to repository"))
        self.actions['editItems'] = self._createAction(self.tr("Edit items"))
        
        
    
    def buildMainMenu(self):
        assert len(self.actions) > 0, "Actions should be already built"
        if self._mainMenu is not None:
            logger.info("Main Menu of this Tool already built")
            return
        
        self._mainMenu = self._createMenu(self.tr("File Browser"), self)
        menu = self._mainMenu
        menu.addAction(self.actions['addFilesToRepo'])
        menu.addAction(self.actions['editItems'])



    def selectedItemIds(self):
        #We use set, because selectedIndexes() may return duplicates
        fileTableRows = set()
        for index in self.ui.filesTableView.selectionModel().selectedIndexes():
            fileTableRows.add(index.row())
        
        itemIds = []
        for row in fileTableRows:
            finfo = self.__fileBrowserTool.listDir()[row]
            for itemId in finfo.itemIds:
                itemIds.append(itemId)
        return itemIds
    
    
    def selectedFiles(self):
        '''
            Returns a list of selected files (abs paths?..).
        '''
        #We use set, because selectedIndexes() may return duplicates
        result = []
        for index in self.ui.filesTableView.selectionModel().selectedIndexes():
            row = index.row()
            finfo = self.__fileBrowserTool.listDir()[row]
            result.append(finfo.path)
        return result
    

class FileBrowserTableModel(QtCore.QAbstractTableModel):
    '''
        A table model for displaying files (not Items) of repository.
    '''
    FILENAME = 0
    TAGS = 1
    USERS = 2
    STATUS = 3
    ITEM_IDS = 4
    RATING = 5
    
    ROLE_FILENAME = Qt.UserRole
    
    def __init__(self, parent, fileBrowserTool, mutex):
        super(FileBrowserTableModel, self).__init__(parent)
        self._fileBrowserTool = fileBrowserTool
        self._mutex = mutex
        

    def rowCount(self, index=QtCore.QModelIndex()):
        return self._fileBrowserTool.filesCount()
    
    def columnCount(self, index=QtCore.QModelIndex()):
        return 5
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                if section == self.FILENAME:
                    return self.tr("Filename")
                elif section == self.TAGS:
                    return self.tr("Tags")
                elif section == self.USERS:
                    return self.tr("Users")
                elif section == self.STATUS:
                    return self.tr("Status")
                elif section == self.ITEM_IDS:
                    return self.tr("Items' ids")
                elif section == self.RATING:
                    return self.tr("Rating")
            else:
                return None
        else:
            return None


    def resetTableRow(self, row):
        self.resetTableRows(row, row)
        
    def resetTableRows(self, topRow, bottomRow):
        topL = self.createIndex(topRow, self.FILENAME)
        bottomR = self.createIndex(bottomRow, self.RATING)
        self.emit(QtCore.SIGNAL("dataChanged(const QModelIndex&, const QModelIndex&)"), topL, bottomR)

    
    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < self.rowCount()):
            return None
                
        column = index.column()
        row = index.row()
        
        try:
            if self._mutex is not None:
                self._mutex.lock()
        
            finfo = self._fileBrowserTool.listDir()[row]
            
            if role == QtCore.Qt.DisplayRole:
                if column == self.FILENAME:
                    return "<html><b>" + finfo.fileBaseName + "</b>" if finfo.isDir() else finfo.fileBaseName
                elif column == self.TAGS:
                    return helpers.to_commalist(finfo.tags)
                elif column == self.ITEM_IDS:
                    return helpers.to_commalist(finfo.itemIds)
                elif column == self.STATUS:
                    return finfo.status
                else:
                    return ""
            if role == FileBrowserTableModel.ROLE_FILENAME:
                return finfo.fileBaseName
          
            return None
        
        finally:
            if self._mutex is not None:
                self._mutex.unlock()
    
    
    