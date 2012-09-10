'''
Created on 07.09.2012
@author: vlkv
'''
from gui.tool_gui import ToolGui
import logging
import consts


logger = logging.getLogger(consts.ROOT_LOGGER + "." + __name__)


class TestToolGui(ToolGui):
    
    def __init__(self, parent, **kwargs):
        logger.debug("TestToolGui init")
        super(TestToolGui, self).__init__(parent, **kwargs)
        pass
    
    
    
    