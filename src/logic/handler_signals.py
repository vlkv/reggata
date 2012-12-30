'''
Created on 04.09.2012
@author: vlkv
'''


class HandlerSignals():
    '''Named constants in this class is not the signal names, but the signal types.
    They are arguments of the following signals: handlerSignal, handlerSignals.
    handlerSignal accepts single signal type. handlerSignals accepts a list of
    signal types. See also WidgetsUpdateManager, ActionHandlerStorage and
    AbstractActionHandler classes.
    '''
    
    ITEM_CREATED = "itemCreated"
    ITEM_CHANGED = "itemChanged"
    ITEM_DELETED = "itemDeleted"
    LIST_OF_FAVORITE_REPOS_CHANGED = "listOfFavoriteReposChanged"
    STATUS_BAR_MESSAGE = "statusBarMessage"
    RESET_SINGLE_ROW = "resetSingleRow"     # TODO: This signal type should be hidden in ItemsTableTool, because it's not global
    RESET_ROW_RANGE = "resetRowRange"       # TODO: This signal type should be hidden in ItemsTableTool too
    REGGATA_CONF_CHANGED = "reggata.conf file has changed"


    @staticmethod
    def allPossibleSignals():
        return [HandlerSignals.ITEM_CREATED,
                HandlerSignals.ITEM_CHANGED,
                HandlerSignals.ITEM_DELETED,
                HandlerSignals.LIST_OF_FAVORITE_REPOS_CHANGED,
                HandlerSignals.STATUS_BAR_MESSAGE,
                HandlerSignals.RESET_SINGLE_ROW,
                HandlerSignals.RESET_ROW_RANGE,
                HandlerSignals.REGGATA_CONF_CHANGED,
                ]
