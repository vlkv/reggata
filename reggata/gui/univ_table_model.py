from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt
from reggata import helpers
from reggata.user_config import UserConfig


def _defaultFormatObj(row, obj, role):
    raise NotImplementedError()


class UnivTableColumn(object):
    def __init__(self, columnId, title, formatObjFun=_defaultFormatObj,
                 delegate=QtGui.QStyledItemDelegate(), setDataFun=None):
        self.id = columnId
        self.title = title
        self._formatObjFun = formatObjFun
        self.delegate = delegate
        self._setDataFun = setDataFun

    def formatObj(self, row, obj, role):
        return self._formatObjFun(row, obj, role)

    def setData(self, obj, row, value, role):
        if self._setDataFun is None:
            return False
        return self._setDataFun(obj, row, value, role)

    def isEditable(self):
        return self._setDataFun is not None



class UnivTableModel(QtCore.QAbstractTableModel):
    '''
        UnivTableModel - is a Universal Table Model, able to display list of any
    objects and also allowing to fine tune which object's fields to display and how.
    '''
    def __init__(self, parent=None):
        super(UnivTableModel, self).__init__(parent)
        self._allColumns = [] # All registered columns
        self._visibleColumns = []
        self._objs = []

    def registerColumn(self, col, isVisible=True):
        assert not helpers.is_none_or_empty(col.id)
        assert not self.isColumnIdRegistered(col.id)
        self._allColumns.append(col)
        if isVisible:
            self._visibleColumns.append(col)

    def column(self, columnVisibleIndex):
        return self._visibleColumns[columnVisibleIndex]

    def columnVisibleIndexById(self, columnId):
        for i in range(self.columnCount()):
            if self.column(i).id == columnId:
                return i
        return None

    def columnById(self, columnId):
        for i in range(len(self._allColumns)):
            if self._allColumns[i].id == columnId:
                return self._allColumns[i]
        return None

    def registeredColumnIds(self):
        res = []
        for i in range(len(self._allColumns)):
            res.append(self._allColumns[i].id)
        return res

    def visibleColumnIds(self):
        res = []
        for i in range(self.columnCount()):
            res.append(self.column(i).id)
        return res

    def isColumnIdRegistered(self, columnId):
        for i in range(len(self._allColumns)):
            if self._allColumns[i].id == columnId:
                return True
        return False

    # Returns True if visibility of the column has changed, False otherwise
    def setColumnVisible(self, columnId, isVisible):
        isVisibleNow = self.isColumnVisible(columnId)
        if isVisibleNow == isVisible:
            return False
        column = self.columnById(columnId)
        if not isVisibleNow and isVisible:
            self._visibleColumns.append(column)
            self.reset()
            return True
        if isVisibleNow and not isVisible:
            columnIndex = self.columnVisibleIndexById(columnId)
            del self._visibleColumns[columnIndex]
            self.reset()
            return True

    def isColumnVisible(self, columnId):
        columnIndex = self.columnVisibleIndexById(columnId)
        return columnIndex is not None

    def setColumnIndex(self, columnId, newIndex):
        c = self.columnById(columnId)
        currentIndex = self.columnVisibleIndexById(columnId)
        if currentIndex is not None:
            del self._visibleColumns[currentIndex]
        self._visibleColumns.insert(newIndex, c)

    def setObjs(self, objs):
        self._objs = objs
        self.reset()

    # rowIndex is a visible index of a row in a table
    def objAtRow(self, rowIndex):
        return self._objs[rowIndex]

    def rowCount(self, index=QtCore.QModelIndex()):
        return len(self._objs)

    # Returns count of visible columns
    def columnCount(self, index=QtCore.QModelIndex()):
        return len(self._visibleColumns)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            columnIndex = section
            column = self._visibleColumns[columnIndex]
            return column.title
        return None


    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < self.rowCount()):
            return None

        visibleCol = index.column()
        column = self.column(visibleCol)

        visibleRow = index.row()
        obj = self.objAtRow(visibleRow)

        res = column.formatObj(visibleRow, obj, role)
        return res

    def flags(self, index):
        res = super(UnivTableModel, self).flags(index)
        c = self.column(index.column())
        if c.isEditable():
            return Qt.ItemFlags(res | QtCore.Qt.ItemIsEditable)
        else:
            return res

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        visibleCol = index.column()
        column = self.column(visibleCol)

        visibleRow = index.row()
        obj = self.objAtRow(visibleRow)

        res = column.setData(obj, visibleRow, value, role)
        if res:
            self.emit(QtCore.SIGNAL("dataChanged(const QModelIndex&, const QModelIndex&)"), index, index)
        return res


    def resetSingleRow(self, row):
        self.resetRowRange(row, row)

    def resetRowRange(self, topRow, bottomRow):
        topL = self.createIndex(topRow, 0)
        bottomR = self.createIndex(bottomRow, len(self._visibleColumns)-1)
        self.emit(QtCore.SIGNAL("dataChanged(const QModelIndex&, const QModelIndex&)"), topL, bottomR)

class UnivTableView(QtGui.QTableView):
    def __init__(self, parent=None):
        super(UnivTableView, self).__init__(parent)
        self.verticalHeader().hide()
        self._model = None

    def setModel(self, origModel):
        model = origModel
        if isinstance(origModel, QtGui.QSortFilterProxyModel):
            model = origModel.sourceModel()
        for i in range(model.columnCount()):
            c = model.column(i)
            if (c.delegate is None):
                continue
            self.setItemDelegateForColumn(i, c.delegate)

        self._model = model

        super(UnivTableView, self).setModel(origModel)

    def restoreColumnsWidth(self, keyPrefix):
        if self._model is None:
            return
        columnIds = self._model.registeredColumnIds()
        for columnId in columnIds:
            columnIndex = self._model.columnVisibleIndexById(columnId)
            if columnIndex is None:
                continue
            self.setColumnWidth(
                columnIndex, int(UserConfig().get(keyPrefix + "." + columnId + ".width", 100)))

    def restoreColumnsVisibility(self, keyPrefix):
        if self._model is None:
            return
        visibleColumns = eval(UserConfig().get(keyPrefix + ".visible_columns", "None")) # None - would mean all columns are visible
        columnIds = self._model.registeredColumnIds()
        for columnId in columnIds:
            if visibleColumns is None:
                self._model.setColumnVisible(columnId, True)
            else:
                self._model.setColumnVisible(columnId, columnId in visibleColumns)

        visibleColumns = self._model.visibleColumnIds()
        i = 0
        for columnId in visibleColumns:
            self._model.setColumnIndex(columnId, i)
            i += 1

    def saveColumnsWidth(self, keyPrefix):
        if self._model is None:
            return
        for i in range(self._model.columnCount()):
            c = self._model.column(i)
            width = self.columnWidth(i)
            if width > 0:
                UserConfig().store(keyPrefix + "." + c.id + ".width", str(width))

    def saveColumnsVisibility(self, keyPrefix):
        if self._model is None:
            return
        visibleColumnIds = []
        for i in range(self._model.columnCount()):
            c = self._model.column(i)
            visibleColumnIds.append(c.id)
        UserConfig().store(keyPrefix + ".visible_columns", visibleColumnIds)


