'''
Created on 19.12.2012
@author: vlkv
'''
import logging
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt
from reggata.gui.tool_gui import ToolGui
import reggata.consts as consts
from reggata.ui.ui_filebrowsergui import Ui_FileBrowserGui
from reggata.helpers import HTMLDelegate
import reggata.helpers as helpers
from reggata.user_config import UserConfig
import os
from reggata.data.commands import FileInfo
from reggata.gui.univ_table_model import UnivTableModel, UnivTableColumn,\
    UnivTableView

logger = logging.getLogger(__name__)


class FileBrowserGui(ToolGui):

    def __init__(self, parent, fileBrowserTool):
        super(FileBrowserGui, self).__init__(parent)
        self.ui = Ui_FileBrowserGui()
        self.ui.setupUi(self)

        self.__fileBrowserTool = fileBrowserTool
        self.__tableModel = None

        self.ui.filesTableView = UnivTableView(self)
        self.ui.tableViewContainer.addWidget(self.ui.filesTableView)

        self.connect(self.ui.filesTableView,
                     QtCore.SIGNAL("activated(const QModelIndex&)"),
                     self.__onTableCellActivated)

        self.resetTableModel(mutex=None)

        self.__context_menu = None
        self.__initContextMenu()

        self.__prevSelRows = []  # This is a stack of row indices


    def resetTableModel(self, mutex):
        self.__tableModel = FileBrowserTableModel(self, self.__fileBrowserTool, mutex)
        self.__tableModel.setObjs(self.__fileBrowserTool.listDir())
        self.ui.filesTableView.setModel(self.__tableModel)
        if self.__fileBrowserTool.repo is not None:
            relCurrDir = os.path.relpath(self.__fileBrowserTool.currDir, self.__fileBrowserTool.repo.base_path)
            self.ui.currDirLineEdit.setText(relCurrDir)
            self.ui.currDirLineEdit.setToolTip(self.__fileBrowserTool.currDir)
        else:
            self.ui.currDirLineEdit.setText("")
            self.ui.currDirLineEdit.setToolTip("")


    def __initContextMenu(self):
        self.buildActions()
        self.__buildContextMenu()
        self.__addContextMenu()


    def __addContextMenu(self):
        assert self.__context_menu is not None, "Context menu is not built"
        self.ui.filesTableView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.connect(self.ui.filesTableView,
                     QtCore.SIGNAL("customContextMenuRequested(const QPoint &)"),
                     self.showContextMenu)


    def showContextMenu(self, pos):
        self.__context_menu.exec_(self.ui.filesTableView.mapToGlobal(pos))



    def __onTableCellActivated(self, index):
        try:
            filename = self.__tableModel.objAtRow(index.row()).fileBaseName
            absFilename = os.path.join(self.__fileBrowserTool.currDir, filename)
            if os.path.isdir(absFilename):
                self.__fileBrowserTool.changeRelDir(filename)
                self.__handleCurrentlySelectedRow(isGoingUp=(filename == ".."),
                                                  newRow=index.row())
            else:
                self.actions['openFile'].trigger()
        except Exception as ex:
            logger.debug("Cannot change current directory: " + str(ex))


    def event(self, e):
        #print(e.__class__.__name__ + " " + str(e.type()))
        if isinstance(e, QtGui.QKeyEvent):
            if e.key() == Qt.Key_Home:
                self.ui.filesTableView.selectRow(0)
                e.accept()
                return True

            elif e.key() == Qt.Key_End:
                rowCount = self.ui.filesTableView.model().rowCount()
                self.ui.filesTableView.selectRow(rowCount - 1)
                e.accept()
                return True
        return super(FileBrowserGui, self).event(e)


    def __handleCurrentlySelectedRow(self, isGoingUp, newRow):
        if isGoingUp:
            assert len(self.__prevSelRows) > 0
            row = self.__prevSelRows.pop()
            self.ui.filesTableView.selectRow(row)
        else:
            self.ui.filesTableView.selectRow(0)
            self.__prevSelRows.append(newRow)


    def resetTableRow(self, row):
        self.__tableModel.resetSingleRow(row)

    def resetTableRows(self, topRow, bottomRow):
        self.__tableModel.resetRowRange(topRow, bottomRow)

    def buildActions(self):
        if len(self.actions) > 0:
            logger.info("Actions already built")
            return

        self.actions['openFile'] = self._createAction(self.tr("Open"))
        self.actions['addFiles'] = self._createAction(self.tr("Add"))
        self.actions['editItems'] = self._createAction(self.tr("Edit"))
        self.actions['moveFiles'] = self._createAction(self.tr("Move"))
        self.actions['renameFile'] = self._createAction(self.tr("Rename"))
        self.actions['deleteFiles'] = self._createAction(self.tr("Delete"))


    def __buildContextMenu(self):
        if self.__context_menu is not None:
            logger.info("Context menu of this Tool already built")
            return

        self.__context_menu = self._createMenu(menuTitle=None, menuParent=self)
        menu = self.__context_menu

        menu.addAction(self.actions['openFile'])
        menu.addAction(self.actions['addFiles'])
        menu.addAction(self.actions['editItems'])
        menu.addAction(self.actions['moveFiles'])
        menu.addAction(self.actions['renameFile'])
        menu.addAction(self.actions['deleteFiles'])


    def selectedItemIds(self):
        #We use set, because selectedIndexes() may return duplicates
        fileTableRows = set()
        for index in self.ui.filesTableView.selectionModel().selectedIndexes():
            fileTableRows.add(index.row())

        itemIds = []
        for row in fileTableRows:
            finfo = self.__fileBrowserTool.listDir()[row]
            if finfo.type == FileInfo.FILE:
                for itemId in finfo.itemIds:
                    itemIds.append(itemId)
            elif finfo.type == FileInfo.DIR:
                assert os.path.isabs(finfo.path)
                itemIds = itemIds + self.__fileBrowserTool.itemIdsForDir(finfo.path)
        return itemIds


    def selectedFiles(self):
        '''
            Returns a list of selected files (abs paths?..).
        '''
        #We use set, because selectedIndexes() may return duplicates
        result = set()
        for index in self.ui.filesTableView.selectionModel().selectedIndexes():
            row = index.row()
            finfo = self.__fileBrowserTool.listDir()[row]
            result.add(finfo.path)
        return list(result)

    def restoreColumnsWidth(self):
        self.ui.filesTableView.restoreColumnsWidth("file_browser")

    def restoreColumnsVisibility(self):
        self.ui.filesTableView.restoreColumnsVisibility("file_browser")

    def saveColumnsWidth(self):
        self.ui.filesTableView.saveColumnsWidth("file_browser")

    def saveColumnsVisibility(self):
        self.ui.filesTableView.saveColumnsVisibility("file_browser")


class FileBrowserTableModel(UnivTableModel):
    '''
        A table model for displaying files (not Items) of repository.
    '''
    FILENAME = "filename"
    TAGS = "tags"
    STATUS = "status"
    ITEM_IDS = "item_ids"


    def __init__(self, parent, fileBrowserTool, mutex):
        super(FileBrowserTableModel, self).__init__(parent)
        self._fileBrowserTool = fileBrowserTool
        self._mutex = mutex
        self.createColumns()

    def createColumns(self):
        def formatFilename(row, finfo, role):
            if role == Qt.DisplayRole:
                return "<html><b>" + finfo.fileBaseName + "</b>" if finfo.isDir() else finfo.fileBaseName
            if role == QtCore.Qt.TextAlignmentRole:
                return int(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            return None
        self.registerColumn(UnivTableColumn(self.FILENAME, self.tr("Filename"), formatFilename,
                                            delegate=helpers.HTMLDelegate(self)))

        def formatTags(row, finfo, role):
            if role == Qt.DisplayRole:
                return helpers.to_commalist(finfo.tags)
            return None
        self.registerColumn(UnivTableColumn(self.TAGS, self.tr("Tags"), formatTags,
                                            delegate=helpers.HTMLDelegate(self)))

        def formatItemIds(row, finfo, role):
            if role == Qt.DisplayRole:
                return helpers.to_commalist(finfo.itemIds)
            return None
        self.registerColumn(UnivTableColumn(self.ITEM_IDS, self.tr("Items' Ids"), formatItemIds,
                                            delegate=helpers.HTMLDelegate(self)))

        def formatStatus(row, finfo, role):
            if role == Qt.DisplayRole:
                return finfo.status
            return None
        self.registerColumn(UnivTableColumn(self.STATUS, self.tr("Status"), formatStatus,
                                            delegate=helpers.HTMLDelegate(self)))


        def data(self, index, role=QtCore.Qt.DisplayRole):
            try:
                if self._mutex is not None:
                    self._mutex.lock()
                return super(FileBrowserTableModel, self).data(index, role)
            finally:
                if self._mutex is not None:
                    self._mutex.unlock()

