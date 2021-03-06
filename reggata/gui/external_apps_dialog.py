'''
Created on 28.09.2012
@author: vlkv
'''
from PyQt4 import QtGui, QtCore
from reggata.ui.ui_externalappsdialog import Ui_ExternalAppsDialog
import reggata.helpers as helpers
from reggata.errors import MsgException
from reggata.logic.ext_app_mgr import ExtAppDescription


class FileExtentionsListValidator(QtGui.QValidator):
    def __init__(self, parent):
        super(FileExtentionsListValidator, self).__init__(parent)

    def validate(self, string, pos):
        strippedString = string.strip()
        if helpers.is_none_or_empty(strippedString):
            return (QtGui.QValidator.Invalid, str(string), pos)

        return (QtGui.QValidator.Acceptable, str(string), pos)



class ExternalAppsDialog(QtGui.QDialog):

    def __init__(self, parent, extAppMgrState, dialogs):
        super(ExternalAppsDialog, self).__init__(parent)
        self.ui = Ui_ExternalAppsDialog()
        self.ui.setupUi(self)

        self.__extAppMgrState = extAppMgrState
        self.__dialogs = dialogs
        self.__read()

        self.connect(self.ui.buttonBox, QtCore.SIGNAL("accepted()"), self.__buttonOkClicked)
        self.connect(self.ui.buttonBox, QtCore.SIGNAL("rejected()"), self.__buttonCancelClicked)

        self.connect(self.ui.comboBoxCategory, QtCore.SIGNAL("currentIndexChanged(int)"),
                     self.__updateCategoryDependentWidgets)

        validator = FileExtentionsListValidator(self.ui.lineEditFileExtensions)
        self.ui.lineEditFileExtensions.setValidator(validator)
        self.connect(self.ui.lineEditFileExtensions, QtCore.SIGNAL("editingFinished()"),
                     self.__parseAndWriteFileExtentions)

        self.connect(self.ui.lineEditAppCmd, QtCore.SIGNAL("textChanged(const QString&)"),
                     self.__writeApplicationCommand)
        self.connect(self.ui.buttonSelectApp, QtCore.SIGNAL("clicked()"),
                     self.__onButtonSelectAppClicked)

        self.connect(self.ui.buttonNewCategory, QtCore.SIGNAL("clicked()"),
                     self.__onButtonNewCategoryClicked)

        self.connect(self.ui.buttonDeleteCategory, QtCore.SIGNAL("clicked()"),
                     self.__onButtonDeleteCategoryClicked)

        self.connect(self.ui.lineEditExtFileBrowserCmd, QtCore.SIGNAL("textChanged(const QString&)"),
                     self.__writeFileBrowserCommand)
        self.connect(self.ui.buttonSelectFileBrowser, QtCore.SIGNAL("clicked()"),
                     self.__onButtonSelectFileBrowserClicked)


    def extAppMgrState(self):
        return self.__extAppMgrState


    def __read(self):
        for appDescription in self.__extAppMgrState.appDescriptions:
            self.ui.comboBoxCategory.addItem(appDescription.filesCategory)

        self.__updateCategoryDependentWidgets(self.__currentCategoryIndex())

        fileBrowserCmd = self.__extAppMgrState.extFileMgrCommandPattern
        self.ui.lineEditExtFileBrowserCmd.setText(fileBrowserCmd)


    def __currentCategoryIndex(self):
        return self.ui.comboBoxCategory.currentIndex()


    def __updateCategoryDependentWidgets(self, groupIndex):
        if groupIndex >= 0:
            appDescription = self.__extAppMgrState.appDescriptions[groupIndex]

            self.ui.lineEditAppCmd.setText(appDescription.appCommandPattern)
            self.ui.lineEditAppCmd.setEnabled(True)

            self.ui.lineEditFileExtensions.setText(
                helpers.to_commalist(appDescription.fileExtentions, apply_each=str, sep=" "))
            self.ui.lineEditFileExtensions.setEnabled(True)

        else:
            self.ui.lineEditAppCmd.setText("")
            self.ui.lineEditAppCmd.setEnabled(False)

            self.ui.lineEditFileExtensions.setText("")
            self.ui.lineEditFileExtensions.setEnabled(False)



    def __parseAndWriteFileExtentions(self):
        index = self.__currentCategoryIndex()
        if index < 0:
            return

        userText = self.ui.lineEditFileExtensions.text().strip()
        assert not helpers.is_none_or_empty(userText), "This is a sign of bug in FileExtentionsListValidator.."

        self.__extAppMgrState.appDescriptions[index].fileExtentions = userText.split()



    def __writeApplicationCommand(self):
        index = self.__currentCategoryIndex()
        if index < 0:
            return
        currentAppCmd = self.__extAppMgrState.appDescriptions[index].appCommandPattern

        try:
            userText = self.ui.lineEditAppCmd.text().strip()
            if helpers.is_none_or_empty(userText):
                raise MsgException(self.tr("Application command should not be empty."))

            self.__extAppMgrState.appDescriptions[index].appCommandPattern = userText

        except Exception as ex:
            helpers.show_exc_info(self, ex)
            self.ui.lineEditAppCmd.setText(currentAppCmd)


    def __writeFileBrowserCommand(self):
        currentCmd = self.__extAppMgrState.extFileMgrCommandPattern
        try:
            userText = self.ui.lineEditExtFileBrowserCmd.text().strip()
            if helpers.is_none_or_empty(userText):
                raise MsgException(self.tr("File Browser command should not be empty."))

            self.__extAppMgrState.extFileMgrCommandPattern = userText

        except Exception as ex:
            helpers.show_exc_info(self, ex)
            self.ui.lineEditExtFileBrowserCmd.setText(currentCmd)



    def __onButtonSelectAppClicked(self):
        executableFile = self.__dialogs.getOpenFileName(self, self.tr("Select application executable file"))
        if not executableFile:
            return

        executableFile = executableFile.strip()
        if " " in executableFile:
            executableFile = '"' + executableFile + '"'
        self.ui.lineEditAppCmd.setText(executableFile + " %f")


    def __onButtonSelectFileBrowserClicked(self):
        executableFile = self.__dialogs.getOpenFileName(self, self.tr("Select file browser executable file"))
        if not executableFile:
            return

        executableFile = executableFile.strip()
        if " " in executableFile:
            executableFile = '"' + executableFile + '"'
        self.ui.lineEditExtFileBrowserCmd.setText(executableFile + " %d")


    def __onButtonNewCategoryClicked(self):
        try:
            categoriesCountBefore = self.ui.comboBoxCategory.count()

            text, isOk = self.__dialogs.execGetTextDialog(self,
                self.tr("Input Dialog"), self.tr("Enter the name for new category of files."),
                defaultText="Category_{}".format(categoriesCountBefore))
            if not isOk:
                return

            if helpers.is_none_or_empty(text):
                raise MsgException(self.tr("Category name should not be empty"))

            if self.__isCategoryExists(text):
                raise MsgException(self.tr("Category with given name already exists. Choose different name."))

            appDescription = ExtAppDescription(text, "<path to executable> %f", [".mp3", ".ogg"])
            self.__extAppMgrState.appDescriptions.append(appDescription)

            self.ui.comboBoxCategory.addItem(text)
            categoriesCountAfter = self.ui.comboBoxCategory.count()
            self.ui.comboBoxCategory.setCurrentIndex(categoriesCountAfter - 1)

        except Exception as ex:
            helpers.show_exc_info(self, ex)


    def __isCategoryExists(self, categoryName):
        for appDescription in self.__extAppMgrState.appDescriptions:
            if appDescription.filesCategory.strip() == categoryName.strip():
                return True
        return False



    def __onButtonDeleteCategoryClicked(self):
        index = self.__currentCategoryIndex()
        if index < 0:
            return
        categoryName = self.__extAppMgrState.appDescriptions[index].filesCategory

        mbResult = self.__dialogs.execMessageBox(self,
            text=self.tr("Do you really want to delete category '{}'?".format(categoryName)),
            buttons=[QtGui.QMessageBox.Yes, QtGui.QMessageBox.No])
        if mbResult != QtGui.QMessageBox.Yes:
            return

        del self.__extAppMgrState.appDescriptions[index]
        self.ui.comboBoxCategory.removeItem(index)


    def __checkCategoriesValid(self):
        self.__extAppMgrState.raiseErrorIfNotValid()


    def __buttonOkClicked(self):
        try:
            self.__checkCategoriesValid()
            return self.accept()

        except Exception as ex:
            helpers.show_exc_info(self, ex)


    def __buttonCancelClicked(self):
        return self.reject()
