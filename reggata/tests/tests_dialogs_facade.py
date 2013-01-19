'''
Created on 28.08.2012
@author: vvolkov
'''
import os
from reggata.logic.abstract_dialogs_facade import AbstractDialogsFacade


class TestsDialogsFacade(AbstractDialogsFacade):

    def __init__(self, selectedFiles=[]):
        self.__selectedFiles = selectedFiles


    def execUserDialog(self, user, gui, dialogMode):
        return True

    def execChangeUserPasswordDialog(self, user, gui):
        return True

    def execItemDialog(self, item, gui, repo, dialogMode):
        if item.data_ref is not None:
            item.data_ref.srcAbsPath = os.path.join(repo.base_path, item.data_ref.url)
            item.data_ref.dstRelPath = os.path.basename(item.data_ref.url)
        return True

    def execItemsDialog(self, items, gui, repo, dialogMode, sameDstPath):
        for item in items:
            if item.data_ref is None:
                continue

            srcAbsPath = os.path.join(repo.base_path, item.data_ref.url)
            item.data_ref.srcAbsPath = srcAbsPath

            if item.data_ref.srcAbsPathToRoot is None:
                item.data_ref.dstRelPath = os.path.basename(srcAbsPath)
            else:
                item.data_ref.dstRelPath = os.path.relpath(srcAbsPath, item.data_ref.srcAbsPathToRoot)
        return True


    def startThreadWithWaitDialog(self, thread, gui, indeterminate):
        thread.run()



    def getOpenFileName(self, gui, textMessageForUser):
        if (len(self.__selectedFiles) == 0):
            return None

        fileName = self.__selectedFiles[0]
        if os.path.exists(fileName) and os.path.isfile(fileName):
            return fileName

        return None

    def getOpenFileNames(self, gui, textMessageForUser):
        if (len(self.__selectedFiles) == 0):
            return []

        fileNames = []
        for path in self.__selectedFiles:
            if os.path.exists(path) and os.path.isfile(path):
                fileNames.append(path)

        return fileNames


    def getExistingDirectory(self, gui, textMessageForUser):
        if (len(self.__selectedFiles) == 0):
            return None

        for path in self.__selectedFiles:
            if os.path.exists(path) and os.path.isdir(path):
                return path

        return None


    def getOpenFilesAndDirs(self, gui, textMessageForUser):
        if (len(self.__selectedFiles) == 0):
            return []

        result = []
        for path in self.__selectedFiles:
            if os.path.exists(path) and (os.path.isfile(path) or os.path.isdir(path)):
                result.append(path)

        return result



    def execMessageBox(self, parent, text, title=None, buttons=None, detailedText=None):
        return buttons[0]
