'''
Created on 08.09.2012
@author: vlkv
'''
from logic.abstract_tool import AbstractTool
from PyQt4 import QtCore
from gui.tag_cloud_gui import TagCloudGui
from logic.handler_signals import HandlerSignals


class TagCloud(AbstractTool):
    
    TOOL_ID = "TagCloudTool"
    
    def __init__(self):
        super(TagCloud, self).__init__()
        
        self._repo = None
        
        self._gui = None
        
        
    def id(self):
        return TagCloud.TOOL_ID

        
    def title(self):
        return self.tr("Tag Cloud Tool")

        
    def createGui(self, guiParent):
        self._gui = TagCloudGui(parent=guiParent, repo=self._repo)
        return self._gui

    
    def __getGui(self):
        return self._gui
    
    gui = property(fget=__getGui)


    def handlerSignals(self):
        return [HandlerSignals.ITEM_CHANGED, HandlerSignals.ITEM_CREATED, 
             HandlerSignals.ITEM_DELETED]


    def enable(self):
        pass

    
    def disable(self):
        pass

    
    def toggleEnableDisable(self, enable):
        if enable:
            self.enable()
        else:
            self.disable()
    
    
    def update(self):
        self._gui.refresh()
        
        
    def setRepo(self, repo):
        self._repo = repo
        self._gui.repo = repo


    def relatedToolIds(self):
        return ["ItemsTableTool"] # Cannot reference to ItemsTable.TOOL_ID because of recursive imports...
    
    
    def connectRelatedTool(self, relatedTool):
        assert relatedTool is not None
        assert relatedTool.id() == "ItemsTableTool"
        
        self._connectItemsTableTool(relatedTool)
        
        
    def _connectItemsTableTool(self, itemsTable):
        self.connect(self._gui, QtCore.SIGNAL("selectedTagsChanged"), 
                     itemsTable.gui.selected_tags_changed)
        self.connect(itemsTable.gui, QtCore.SIGNAL("queryTextResetted"), 
                     self._gui.reset)
        
            
    
