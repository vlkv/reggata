'''
Created on 19.12.2012
@author: vlkv
'''
from gui.tool_gui import ToolGui
import logging
import consts
import ui_filebrowsergui

logger = logging.getLogger(consts.ROOT_LOGGER + "." + __name__)

class FileBrowserGui(ToolGui):
    

    def __init__(self, parent, fileBrowserTool):
        super(FileBrowserGui, self).__init__(parent)
        self.ui = ui_filebrowsergui.Ui_FileBrowserGui()
        self.ui.setupUi(self)
        
        self.__fileBrowserTool = fileBrowserTool
        
        
        
        