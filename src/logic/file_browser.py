'''
Created on 19.12.2012
@author: vlkv
'''
from logic.abstract_tool import AbstractTool
from gui.file_browser_gui import FileBrowserGui
import logging
import consts

logger = logging.getLogger(consts.ROOT_LOGGER + "." + __name__)

class FileBrowser(AbstractTool):

    TOOL_ID = "FileBrowserTool"

    def __init__(self):
        super(FileBrowser, self).__init__()
        self._gui = None
        self._repo = None
        self._user = None
        
        
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
            # TODO: recreate File Browser Gui
            pass
        else:
            # TODO: reset File Browser Gui
            pass
        
        
    @property
    def user(self):
        return self._user
    
    def setUser(self, user):
        self._user = user
        # TODO: update Gui according to the user change
        
        
        
        