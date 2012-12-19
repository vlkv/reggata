'''
Created on 19.12.2012
@author: vlkv
'''
from gui.tool_gui import ToolGui


class FileBrowserGui(ToolGui):
    

    def __init__(self, parent, fileBrowserTool):
        super(FileBrowserGui, self).__init__(parent)
        
        self.__fileBrowserTool = fileBrowserTool
        
        