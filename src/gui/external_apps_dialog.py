'''
Created on 28.09.2012
@author: vlkv
'''
from PyQt4 import QtGui
from ui_externalappsdialog import Ui_ExternalAppsDialog

class ExternalAppsDialog(QtGui.QDialog):

    def __init__(self, parent, extAppMgrState):
        super(ExternalAppsDialog, self).__init__(parent)
        self.ui = Ui_ExternalAppsDialog()
        self.ui.setupUi(self)
        
        self.__extAppMgrState = extAppMgrState
        self.__read()
        
        
    
    
    def __read(self):
        for appDescription in self.__extAppMgrState.appDescriptions:
            
            self.ui.comboBoxGroups.addItem(appDescription.filesCategory)
            
        # TODO...