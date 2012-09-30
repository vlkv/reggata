'''
Created on 28.09.2012
@author: vlkv
'''
from PyQt4 import QtGui, QtCore
from ui_externalappsdialog import Ui_ExternalAppsDialog
import helpers
from errors import MsgException


class FileExtentionsListValidator(QtGui.QValidator):
    def __init__(self, parent):
        super(FileExtentionsListValidator, self).__init__(parent)
    
    def validate(self, string, pos):
        strippedString = string.strip()
        if helpers.is_none_or_empty(strippedString):
            return (QtGui.QValidator.Invalid, str(string), pos)
        
        return (QtGui.QValidator.Acceptable, str(string), pos)
    
        

class ExternalAppsDialog(QtGui.QDialog):

    def __init__(self, parent, extAppMgrState):
        super(ExternalAppsDialog, self).__init__(parent)
        self.ui = Ui_ExternalAppsDialog()
        self.ui.setupUi(self)
        
        self.__extAppMgrState = extAppMgrState
        self.__read()
        
        self.connect(self.ui.comboBoxCategory, QtCore.SIGNAL("currentIndexChanged(int)"), 
                     self.__updateCategoryDependentWidgets)
        
        validator = FileExtentionsListValidator(self.ui.lineEditFileExtensions)
        self.ui.lineEditFileExtensions.setValidator(validator)
        self.connect(self.ui.lineEditFileExtensions, QtCore.SIGNAL("editingFinished()"),
                     self.__parseAndWriteFileExtentions)
        
        self.connect(self.ui.lineEditAppCmdPattern, QtCore.SIGNAL("textChanged(const QString&)"),
                     self.__writeApplicationCommandPattern)
                     
        
        
        
    def __read(self):
        for appDescription in self.__extAppMgrState.appDescriptions:
            self.ui.comboBoxCategory.addItem(appDescription.filesCategory)
        
        self.__updateCategoryDependentWidgets(self.__currentCategoryIndex())
    
    def __currentCategoryIndex(self):
        return self.ui.comboBoxCategory.currentIndex()
        
    
    def __updateCategoryDependentWidgets(self, groupIndex):
        
        appDescription = self.__extAppMgrState.appDescriptions[groupIndex]
        
        self.ui.lineEditAppCmdPattern.setText(appDescription.appCommandPattern)
        self.ui.lineEditFileExtensions.setText(
            helpers.to_commalist(appDescription.fileExtentions, apply_each=str, sep=" "))
        
        
    def __parseAndWriteFileExtentions(self):
        userText = self.ui.lineEditFileExtensions.text().strip()
        assert not helpers.is_none_or_empty(userText), "This is a sign of bug in FileExtentionsListValidator.."
        
        extentions = userText.split()
        index = self.__currentCategoryIndex()
        self.__extAppMgrState.appDescriptions[index].fileExtentions = extentions
        
    
            
    def __writeApplicationCommandPattern(self):
        
        index = self.__currentCategoryIndex()
        currentAppCmd = self.__extAppMgrState.appDescriptions[index].appCommandPattern
        
        try:
            userText = self.ui.lineEditAppCmdPattern.text().strip()
            if helpers.is_none_or_empty(userText):
                raise MsgException(self.tr("Application command pattern should not be empty."))
            
            self.__extAppMgrState.appDescriptions[index].appCommandPattern = userText
            
        except Exception as ex:
            helpers.show_exc_info(self, ex)
            self.ui.lineEditAppCmdPattern.setText(currentAppCmd)
            
        
        
        
        
        
        