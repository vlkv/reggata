'''
Created on 19.12.2012
@author: vlkv
'''
from gui.tool_gui import ToolGui
import logging
import consts

logger = logging.getLogger(consts.ROOT_LOGGER + "." + __name__)

class FileBrowserGui(ToolGui):
    

    def __init__(self, parent, fileBrowserTool):
        super(FileBrowserGui, self).__init__(parent)
        
        self.__fileBrowserTool = fileBrowserTool
        
        