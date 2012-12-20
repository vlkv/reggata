'''
Created on 19.12.2012
@author: vlkv
'''
from gui.tool_gui import ToolGui
import logging
import consts
import ui_filebrowsergui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt

logger = logging.getLogger(consts.ROOT_LOGGER + "." + __name__)

class FileBrowserGui(ToolGui):
    

    def __init__(self, parent, fileBrowserTool):
        super(FileBrowserGui, self).__init__(parent)
        self.ui = ui_filebrowsergui.Ui_FileBrowserGui()
        self.ui.setupUi(self)
        
        self.__fileBrowserTool = fileBrowserTool
        self.connect(self.ui.filesTableView, QtCore.SIGNAL("activated(const QModelIndex&)"), self.__onMouseDoubleClick)
        self.resetTableModel()
        
        
    def resetTableModel(self):
        self.ui.filesTableView.setModel(FileBrowserTableModel(self, self.__fileBrowserTool))
        
        
    def __onMouseDoubleClick(self, index):
        filename = self.ui.filesTableView.model().data(index, FileBrowserTableModel.ROLE_FILENAME)
        try:
            self.__fileBrowserTool.changeRelDir(filename)
        except Exception as ex:
            logger.debug("Cannot change current directory: " + str(ex))


class FileBrowserTableModel(QtCore.QAbstractTableModel):
    '''
        A table model for displaying files (not Items) of repository.
    '''
    FILENAME = 0
    TAGS = 1
    USERS = 2
    STATUS = 3
    RATING = 4
    
    ROLE_FILENAME = Qt.UserRole
    
    def __init__(self, parent, fileBrowserTool):
        super(FileBrowserTableModel, self).__init__(parent)
        self._fileBrowserTool = fileBrowserTool
        

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
                elif section == self.RATING:
                    return self.tr("Rating")
            else:
                return None
        else:
            return None

    
    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < self.rowCount()):
            return None
                
        column = index.column()
        row = index.row()
        fname = self._fileBrowserTool.listDir()[row]
        
        if role == QtCore.Qt.DisplayRole:
            if column == self.FILENAME:
                return fname
            else:
                return ""
        if role == FileBrowserTableModel.ROLE_FILENAME:
            return fname
      
        return None
    
    
    