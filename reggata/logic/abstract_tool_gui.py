'''
Created on 07.09.2012
@author: vlkv
'''
import logging
import reggata.consts as consts

logger = logging.getLogger(consts.ROOT_LOGGER + "." + __name__)


class AbstractToolGui(object):

    def __init__(self):
        logger.debug("AbstractToolGui init")
        super(AbstractToolGui, self).__init__()
