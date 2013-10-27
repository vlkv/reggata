from PyQt4 import QtCore, Qt

def _raise(ex):
    raise ex

class UnivTableColumn(object):
    def __init__(self, title, formatObjFun=(lambda obj, role : _raise(NotImplementedError())) ):
        self.title = title
        self._formatObjFun = formatObjFun

    def formatObj(self, obj, role):
        return self._formatObjFun(obj, role)



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
        self._columns.append(col)

    def populateObjs(self):
        raise NotImplementedError("Reimplement in a child class. Fun must return list of objects to be displayed in the table")

    def rowCount(self, index=QtCore.QModelIndex()):
        return len(self._objs)

    def columnCount(self, index=QtCore.QModelIndex()):
        return len(self._columns)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            columnIndex = section
            column = self._columns[columnIndex]
            return column.title
        elif orientation == Qt.Vertical:
            rowIndex = section
            return rowIndex + 1
        else:
            return None


    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < self.rowCount()):
            return None

        visibleCol = index.column()
        column = self._columns[visibleCol]

        visibleRow = index.row()
        obj = self._objs[visibleRow]

        res = column.formatObj(obj, role)
        return res

    #def flags(self, index):


    #def setData(self, index, value, role=QtCore.Qt.EditRole):


    def resetSingleRow(self, row):
        self.resetRowRange(row, row)

    def resetRowRange(self, topRow, bottomRow):
        topL = self.createIndex(topRow, 0)
        bottomR = self.createIndex(bottomRow, len(self._columns)-1)
        self.emit(QtCore.SIGNAL("dataChanged(const QModelIndex&, const QModelIndex&)"), topL, bottomR)

