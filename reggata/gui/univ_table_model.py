from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt
from reggata import helpers


def _defaultFormatObj(row, obj, role):
    raise NotImplementedError()


class UnivTableColumn(object):
    def __init__(self, columnId, title, formatObjFun=_defaultFormatObj, delegate=QtGui.QStyledItemDelegate()):
        self.id = columnId
        self.title = title
        self._formatObjFun = formatObjFun
        self.delegate = delegate

    def formatObj(self, row, obj, role):
        return self._formatObjFun(row, obj, role)



class UnivTableModel(QtCore.QAbstractTableModel):
    '''
        UnivTableModel - is a Universal Table Model, able to display list of any
    objects and also allowing to fine tune which object's fields to display and how.
    '''
    def __init__(self):
        super(UnivTableModel, self).__init__()
        self._columns = []
        self._objs = []

    def addColumn(self, col):
        assert not helpers.is_none_or_empty(col.id)
        assert self.findColumnById(col.id) is None
        self._columns.append(col)

    def findColumnIndexById(self, columnId):
        for i in range(self.columnCount()):
            if self.column(i).id == columnId:
                return i
        return None

    def findColumnById(self, columnId):
        for i in range(self.columnCount()):
            if self.column(i).id == columnId:
                return self.column(i)
        return None

    def registeredColumnIds(self):
        res = []
        for i in range(self.columnCount()):
            res.append(self.column(i).id)
        return res

    def column(self, columnIndex):
        return self._columns[columnIndex]

    def setObjs(self, objs):
        self._objs = objs
        self.reset()

    def objAtRow(self, rowIndex):
        return self._objs[rowIndex]

    def rowCount(self, index=QtCore.QModelIndex()):
        return len(self._objs)

    def columnCount(self, index=QtCore.QModelIndex()):
        return len(self._columns)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            columnIndex = section
            column = self._columns[columnIndex]
            return column.title
        return None


    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < self.rowCount()):
            return None

        visibleCol = index.column()
        column = self._columns[visibleCol]

        visibleRow = index.row()
        obj = self._objs[visibleRow]

        res = column.formatObj(visibleRow, obj, role)
        return res

    #def flags(self, index):


    #def setData(self, index, value, role=QtCore.Qt.EditRole):


    def resetSingleRow(self, row):
        self.resetRowRange(row, row)

    def resetRowRange(self, topRow, bottomRow):
        topL = self.createIndex(topRow, 0)
        bottomR = self.createIndex(bottomRow, len(self._columns)-1)
        self.emit(QtCore.SIGNAL("dataChanged(const QModelIndex&, const QModelIndex&)"), topL, bottomR)

class UnivTableView(QtGui.QTableView):
    def __init__(self, parent=None):
        super(UnivTableView, self).__init__(parent)
        self.verticalHeader().hide()

    def setModel(self, model):
        for i in range(model.columnCount()):
            c = model.column(i)
            if (c.delegate is None):
                continue
            self.setItemDelegateForColumn(i, c.delegate)

        super(UnivTableView, self).setModel(model)

