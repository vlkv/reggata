'''
Created on 28.09.2012
@author: vlkv
'''
from PyQt4 import QtGui, QtCore
from ui_externalappsdialog import Ui_ExternalAppsDialog
import helpers

class ExternalAppsDialog(QtGui.QDialog):

    def __init__(self, parent, extAppMgrState):
        super(ExternalAppsDialog, self).__init__(parent)
        self.ui = Ui_ExternalAppsDialog()
        self.ui.setupUi(self)
        
        self.__extAppMgrState = extAppMgrState
        self.__read()
        
        self.connect(self.ui.comboBoxGroups, QtCore.SIGNAL("currentIndexChanged(int)"), 
                     self.__updateGroupDependentWidgets)
        
    
    
    def __read(self):
        for appDescription in self.__extAppMgrState.appDescriptions:
            self.ui.comboBoxGroups.addItem(appDescription.filesCategory)
        
        i = self.ui.comboBoxGroups.currentIndex()    
        
        self.__updateGroupDependentWidgets(i)
    
    
    def __updateGroupDependentWidgets(self, groupSelectedIndex):
        
        appDescription = self.__extAppMgrState.appDescriptions[groupSelectedIndex] 
        
        self.ui.lineEditApplicationPath.setText(appDescription.appCommandPattern)
        self.ui.lineEditFileExtensions.setText(
            helpers.to_commalist(appDescription.fileExtentions, apply_each=str, sep="; "))
        
        
        