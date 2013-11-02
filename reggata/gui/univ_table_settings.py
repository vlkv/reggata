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

        self._visibleIds = self._tableModel.visibleColumnIds()
        self._hiddenIds = []
        for columnId in self._tableModel.registeredColumnIds():
            if columnId in self._visibleIds:
                continue
            self._hiddenIds.append(columnId)

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
        for columnId in self._hiddenIds:
            item = QtGui.QListWidgetItem(columnId)
            self.ui.listWidgetHiddenColumns.addItem(item)

        self.ui.listWidgetVisibleColumns.clear()
        for columnId in self._visibleIds:
            item = QtGui.QListWidgetItem(columnId)
            self.ui.listWidgetVisibleColumns.addItem(item)


    def _makeColumnVisible(self):
        selItems = self.ui.listWidgetHiddenColumns.selectedItems()
        if len(selItems) == 0:
            return
        for item in selItems:
            columnId = item.text()
            self._hiddenIds.remove(columnId)
            self._visibleIds.append(columnId)
        self._readData()


    def _makeColumnHidden(self):
        selItems = self.ui.listWidgetVisibleColumns.selectedItems()
        if len(selItems) == 0:
            return
        for item in selItems:
            columnId = item.text()
            self._visibleIds.remove(columnId)
            self._hiddenIds.append(columnId)
        self._readData()



    def _moveColumnUp(self):
        selIndexes = self.ui.listWidgetVisibleColumns.selectedIndexes()
        if len(selIndexes) != 1:
            return
        selIndex = selIndexes[0].row()
        if selIndex == 0:
            return
        columnId = self._visibleIds[selIndex]
        del self._visibleIds[selIndex]
        self._visibleIds.insert(selIndex-1, columnId)
        self._readData()
        self.ui.listWidgetVisibleColumns.setCurrentRow(selIndex-1)



    def _moveColumnDown(self):
        selIndexes = self.ui.listWidgetVisibleColumns.selectedIndexes()
        if len(selIndexes) != 1:
            return
        selIndex = selIndexes[0].row()
        if selIndex == len(self._visibleIds) - 1:
            return
        columnId = self._visibleIds[selIndex]
        del self._visibleIds[selIndex]
        self._visibleIds.insert(selIndex+1, columnId)
        self._readData()
        self.ui.listWidgetVisibleColumns.setCurrentRow(selIndex+1)



    def _buttonAccept(self):
        res = []
        for i in range(len(self._visibleIds)):
            res.append(self._visibleIds[i])
        UserConfig().store(self._keyPrefix + ".visible_columns", res)
        self.accept()

    def _buttonReject(self):
        self.reject()




