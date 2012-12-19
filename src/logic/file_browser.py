'''
Created on 19.12.2012
@author: vlkv
'''
from logic.abstract_tool import AbstractTool
from gui.file_browser_gui import FileBrowserGui

class FileBrowser(AbstractTool):

    TOOL_ID = "FileBrowserTool"

    def __init__(self):
        super(FileBrowser, self).__init__()
        self._repo = None
        self._gui = None
        
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