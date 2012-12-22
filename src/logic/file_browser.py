'''
Created on 19.12.2012
@author: vlkv
'''
from logic.abstract_tool import AbstractTool
from gui.file_browser_gui import FileBrowserGui
import logging
import consts
from errors import NoneError, NotExistError
import os
import helpers
from data.commands import FileInfo

logger = logging.getLogger(consts.ROOT_LOGGER + "." + __name__)

class FileBrowser(AbstractTool):

    TOOL_ID = "FileBrowserTool"

    def __init__(self):
        super(FileBrowser, self).__init__()
        self._gui = None
        self._repo = None
        self._user = None
        self._currDir = None
        self._listCache = None
        
        
    def id(self):
        return self.TOOL_ID
    
    def title(self):
        return self.tr("File Browser")
    
    def createGui(self, guiParent):
        self._gui = FileBrowserGui(guiParent, self)
        return self._gui
    
    def __getGui(self):
        return self._gui
    gui = property(fget=__getGui)
    
    
    @property
    def repo(self):
        return self._repo
        
    def setRepo(self, repo):
        self._repo = repo
        if repo is not None:
            self.changeDir(repo.base_path)
        else:
            self.unsetDir()

    @property
    def user(self):
        return self._user
    
    def setUser(self, user):
        self._user = user
        # TODO: update Gui according to the user change
        
    
    @property
    def currDir(self):
        if self._currDir is None:
            raise NoneError()
        return self._currDir
    
    
    def repoBasePath(self):
        if self._repo is None:
            raise NoneError()
        return self._repo.base_path


    def listDir(self):
        if self._currDir is None:
            return []
        if self._listCache is None:
            self._rebuildListCache()
        return self._listCache
    
    def filesCount(self):
        if self._currDir is None:
            return 0
        if self._listCache is None:
            self._rebuildListCache()
        return len(self._listCache)
    
    def _rebuildListCache(self):
        assert self._currDir is not None
        result=[FileInfo("..", FileInfo.DIR)]
        for fname in os.listdir(self._currDir):
            absPath = os.path.join(self._currDir, fname)
            if os.path.isfile(absPath):
                result.append(FileInfo(absPath, FileInfo.FILE))
            elif os.path.isdir(absPath):
                result.append(FileInfo(absPath, FileInfo.DIR))
        self._listCache = result
    
    
    def changeDirUp(self):
        self.changeDir("..")
    
    def changeRelDir(self, relativeDir):
        absDir = os.path.join(self._currDir, relativeDir)
        absDir = os.path.normpath(absDir)
        self.changeDir(absDir)
    
    def changeDir(self, directory):
        if directory == ".":
            directory = self._currDir
            
        if directory == "..":
            directory, _ = os.path.split(self._currDir)
            
        if not os.path.exists(directory):
            raise NotExistError(directory + " not exists on the file system.")
        
        if not helpers.is_internal(directory, self.repoBasePath()):
            raise ValueError(directory +  " is outside the repository.")
        
        if os.path.isfile(directory):
            raise ValueError(directory + " is not a directory but a file.")
        
        assert os.path.isabs(directory)
        self._currDir = directory
        self._listCache = None
        self._gui.resetTableModel()
        
    def unsetDir(self):
        self._currDir = None
        self._listCache = None
        self._gui.resetTableModel()
    
    
    