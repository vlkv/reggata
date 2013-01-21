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
from reggata.helpers import HTMLDelegate
import reggata.helpers as helpers
from reggata.user_config import UserConfig

logger = logging.getLogger(consts.ROOT_LOGGER + "." + __name__)


class FileBrowserGui(ToolGui):

    def __init__(self, parent, fileBrowserTool):
        super(FileBrowserGui, self).__init__(parent)
        self.ui = Ui_FileBrowserGui()
        self.ui.setupUi(self)

        self.__fileBrowserTool = fileBrowserTool
        self.__tableModel = None

        self.ui.filesTableView.setItemDelegate(HTMLDelegate(self))
        self.connect(self.ui.filesTableView,
                     QtCore.SIGNAL("activated(const QModelIndex&)"),
                     self.__onTableCellActivated)

        self.resetTableModel(mutex=None)

        self.__context_menu = None
        self.__initContextMenu()

        self.__prevSelRows = []  # This is a stack of row indices


    def resetTableModel(self, mutex):
        self.__tableModel = FileBrowserTableModel(self, self.__fileBrowserTool, mutex)
        self.ui.filesTableView.setModel(self.__tableModel)


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
            filename = self.ui.filesTableView.model().data(index, FileBrowserTableModel.ROLE_FILENAME)
            self.__fileBrowserTool.changeRelDir(filename)
            self.__handleCurrentlySelectedRow(isGoingUp=(filename == ".."),
                                              newRow=index.row())
        except Exception as ex:
            logger.debug("Cannot change current directory: " + str(ex))


    def __handleCurrentlySelectedRow(self, isGoingUp, newRow):
        if isGoingUp:
            assert len(self.__prevSelRows) > 0
            row = self.__prevSelRows.pop()
            self.ui.filesTableView.selectRow(row)
        else:
            self.ui.filesTableView.selectRow(0)
            self.__prevSelRows.append(newRow)


    def resetTableRow(self, row):
        self.__tableModel.resetTableRow(row)

    def resetTableRows(self, topRow, bottomRow):
        self.__tableModel.resetTableRows(topRow, bottomRow)

    def buildActions(self):
        if len(self.actions) > 0:
            logger.info("Actions already built")
            return

        self.actions['openFile'] = self._createAction(self.tr("Open"))
        self.actions['addFilesToRepo'] = self._createAction(self.tr("Add files"))
        self.actions['editItems'] = self._createAction(self.tr("Edit items"))


    def __buildContextMenu(self):
        if self.__context_menu is not None:
            logger.info("Context menu of this Tool already built")
            return

        self.__context_menu = self._createMenu(menuTitle=None, menuParent=self)
        menu = self.__context_menu

        menu.addAction(self.actions['openFile'])
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


    def restoreColumnsWidths(self):
        self.ui.filesTableView.setColumnWidth(FileBrowserTableModel.FILENAME, int(UserConfig().get("file_browser.FILENAME.width", 450)))
        self.ui.filesTableView.setColumnWidth(FileBrowserTableModel.TAGS, int(UserConfig().get("file_browser.TAGS.width", 300)))
        self.ui.filesTableView.setColumnWidth(FileBrowserTableModel.USERS, int(UserConfig().get("file_browser.USERS.width", 100)))
        self.ui.filesTableView.setColumnWidth(FileBrowserTableModel.STATUS, int(UserConfig().get("file_browser.STATUS.width", 100)))
        self.ui.filesTableView.setColumnWidth(FileBrowserTableModel.ITEM_IDS, int(UserConfig().get("file_browser.ITEM_IDS.width", 100)))
        self.ui.filesTableView.setColumnWidth(FileBrowserTableModel.RATING, int(UserConfig().get("file_browser.RATING.width", 200)))

    def saveColumnsWidths(self):
        width = self.ui.filesTableView.columnWidth(FileBrowserTableModel.FILENAME)
        if width > 0:
            UserConfig().store("file_browser.FILENAME.width", str(width))

        width = self.ui.filesTableView.columnWidth(FileBrowserTableModel.TAGS)
        if width > 0:
            UserConfig().store("file_browser.TAGS.width", str(width))

        width = self.ui.filesTableView.columnWidth(FileBrowserTableModel.USERS)
        if width > 0:
            UserConfig().store("file_browser.USERS.width", str(width))

        width = self.ui.filesTableView.columnWidth(FileBrowserTableModel.STATUS)
        if width > 0:
            UserConfig().store("file_browser.STATUS.width", str(width))

        width = self.ui.filesTableView.columnWidth(FileBrowserTableModel.ITEM_IDS)
        if width > 0:
            UserConfig().store("file_browser.ITEM_IDS.width", str(width))

        width = self.ui.filesTableView.columnWidth(FileBrowserTableModel.RATING)
        if width > 0:
            UserConfig().store("file_browser.RATING.width", str(width))



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
