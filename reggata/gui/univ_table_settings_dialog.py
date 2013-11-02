from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt
from reggata.ui.ui_univtablesettingsdialog import Ui_UnivTableSettingsDialog
from reggata.user_config import UserConfig

class UnivTableSettigsDialog(QtGui.QDialog):
    def __init__(self, univTableModel, settingsKeyPrefix, parent=None):
        super(UnivTableSettigsDialog, self).__init__(parent)
        assert univTableModel is not None
        self._tableModel = univTableModel

        self._keyPrefix = settingsKeyPrefix

        self._visibleIds = []
        for columnId in self._tableModel.visibleColumnIds():
            c = self._tableModel.columnById(columnId)
            self._visibleIds.append((columnId, c.title))

        self._hiddenIds = []
        for columnId in self._tableModel.registeredColumnIds():
            if self._tableModel.isColumnVisible(columnId):
                continue
            c = self._tableModel.columnById(columnId)
            self._hiddenIds.append((columnId, c.title))

        self.ui = Ui_UnivTableSettingsDialog()
        self.ui.setupUi(self)

        self.connect(self.ui.buttonBox, QtCore.SIGNAL("accepted()"), self._buttonAccept)
        self.connect(self.ui.buttonBox, QtCore.SIGNAL("rejected()"), self._buttonReject)
        self.connect(self.ui.pushButtonMakeVisible, QtCore.SIGNAL("clicked()"), self._makeColumnVisible)
        self.connect(self.ui.pushButtonMakeHidden, QtCore.SIGNAL("clicked()"), self._makeColumnHidden)
        self.connect(self.ui.pushButtonMoveUp, QtCore.SIGNAL("clicked()"), self._moveColumnUp)
        self.connect(self.ui.pushButtonMoveDown, QtCore.SIGNAL("clicked()"), self._moveColumnDown)

        self._readData()


    def _readData(self):
        self.ui.listWidgetHiddenColumns.clear()
        for (columnId, title) in self._hiddenIds:
            item = QtGui.QListWidgetItem(title)
            self.ui.listWidgetHiddenColumns.addItem(item)

        self.ui.listWidgetVisibleColumns.clear()
        for (columnId, title) in self._visibleIds:
            item = QtGui.QListWidgetItem(title)
            self.ui.listWidgetVisibleColumns.addItem(item)


    def _makeColumnVisible(self):
        indexes = self.ui.listWidgetHiddenColumns.selectedIndexes()
        if len(indexes) == 0:
            return

        colsToProcess = []
        for index in indexes:
            columnId, title = self._hiddenIds[index.row()]
            colsToProcess.append((columnId, title))

        for (columnId, title) in colsToProcess:
            self._visibleIds.append((columnId, title))
            i = self._findIndexByColumnId(columnId, self._hiddenIds)
            del self._hiddenIds[i]
        self._readData()




    def _makeColumnHidden(self):
        indexes = self.ui.listWidgetVisibleColumns.selectedIndexes()
        if len(indexes) == 0:
            return

        colsToProcess = []
        for index in indexes:
            columnId, title = self._visibleIds[index.row()]
            colsToProcess.append((columnId, title))

        for (columnId, title) in colsToProcess:
            self._hiddenIds.append((columnId, title))
            i = self._findIndexByColumnId(columnId, self._visibleIds)
            del self._visibleIds[i]
        self._readData()


    def _findIndexByColumnId(self, columnId, collection):
        for i in range(len(collection)):
            cId, _cTitle = collection[i]
            if cId == columnId:
                return i
        return None


    def _moveColumnUp(self):
        indexes = self.ui.listWidgetVisibleColumns.selectedIndexes()
        if len(indexes) != 1:
            return
        index = indexes[0].row()
        if index == 0:
            return
        columnId, title = self._visibleIds[index]
        del self._visibleIds[index]
        self._visibleIds.insert(index-1, (columnId, title))
        self._readData()
        self.ui.listWidgetVisibleColumns.setCurrentRow(index-1)



    def _moveColumnDown(self):
        indexes = self.ui.listWidgetVisibleColumns.selectedIndexes()
        if len(indexes) != 1:
            return
        index = indexes[0].row()
        if index == len(self._visibleIds) - 1:
            return
        columnId, title = self._visibleIds[index]
        del self._visibleIds[index]
        self._visibleIds.insert(index+1, (columnId, title))
        self._readData()
        self.ui.listWidgetVisibleColumns.setCurrentRow(index+1)



    def _buttonAccept(self):
        res = []
        for columnId, title in self._visibleIds:
            res.append(columnId)
        UserConfig().store(self._keyPrefix + ".visible_columns", res)
        self.accept()

    def _buttonReject(self):
        self.reject()




