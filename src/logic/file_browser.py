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
from data.commands import FileInfo, GetFileInfoCommand
from PyQt4 import QtCore
import traceback

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
        self._mutex = None
        self._thread = None
        
        
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
        
        def resetSingleGuiTableRow(row):
            self._gui.resetSingleRow(row)
            
        
        assert self._currDir is not None
        result=[FileInfo("..", FileInfo.DIR)]
        for fname in os.listdir(self._currDir):
            absPath = os.path.join(self._currDir, fname)
            if os.path.isfile(absPath):
                result.append(FileInfo(absPath, FileInfo.FILE))
            elif os.path.isdir(absPath):
                result.append(FileInfo(absPath, FileInfo.DIR))
        self._listCache = result
        
        logger.debug("_rebuildListCache is about to start the FileInfoSearcherThread")
        self._thread = FileInfoSearcherThread(self, self._repo, self._listCache, self._mutex)
        self.connect(self._thread, QtCore.SIGNAL("progress"),
                         lambda percents, row: resetSingleGuiTableRow(row))
        self._thread.start()
        #self._thread.run()
    
    
    
    
    def changeDirUp(self):
        self.changeDir("..")
    
    def changeRelDir(self, relativeDir):
        absDir = os.path.join(self._currDir, relativeDir)
        absDir = os.path.normpath(absDir)
        self.changeDir(absDir)
    
    def changeDir(self, directory):
        if self._thread is not None:
            self._thread.interrupt = True
            self._thread.wait()
        
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
        self._mutex = QtCore.QMutex()
        self._gui.resetTableModel(self._mutex)
        
    def unsetDir(self):
        if self._thread is not None:
            self._thread.interrupt = True
            self._thread.wait()
        
        self._currDir = None
        self._listCache = None
        self._mutex = None
        self._gui.resetTableModel(self._mutex)
    
    
class FileInfoSearcherThread(QtCore.QThread):
    def __init__(self, parent, repo, finfos, mutex):
        super(FileInfoSearcherThread, self).__init__(parent)
        self.repo = repo
        self.finfos = finfos
        self.mutex = mutex
        self.interrupt = False

    def run(self):
        
        logger.debug("FileInfoSearcherThread started. There are {} files to process".format(len(self.finfos)))
        
        uow = self.repo.createUnitOfWork()
        try:
            i = 0
            for finfo in self.finfos:
                if self.interrupt:
                    break
                if finfo.type != FileInfo.FILE:
                    continue
                relPath = os.path.relpath(finfo.path, self.repo.base_path)
                cmd = GetFileInfoCommand(relPath)
                newFinfo = uow.executeCommand(cmd)
                
                self.mutex.lock()
                finfo.tags = newFinfo.tags
                finfo.fields = newFinfo.fields
                finfo.type = newFinfo.type
                finfo.status = newFinfo.status
                self.mutex.unlock()
                
                i = i + 1
                self.emit(QtCore.SIGNAL("progress"), int(100.0*float(i)/len(self.finfos)), i)
                logger.debug("FileInfoSearcherThread progress: {}%, row={}".format(int(100.0*float(i)/len(self.finfos)), i))
                
        except Exception as ex:
            self.emit(QtCore.SIGNAL("exception"), traceback.format_exc())
            logger.debug("FileInfoSearcherThread exception: {}".format(ex))
        
        finally:
            uow.close()
            self.emit(QtCore.SIGNAL("finished"))
            logger.debug("FileInfoSearcherThread done.")
            
        
    
    