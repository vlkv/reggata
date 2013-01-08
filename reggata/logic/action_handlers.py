# -*- coding: utf-8 -*-
'''
Created on 23.07.2012
@author: vlkv
'''
from PyQt4 import QtCore

class ActionHandlerStorage():
    def __init__(self, widgetsUpdateManager):
        self.__actions = dict()
        self.__widgetsUpdateManager = widgetsUpdateManager

    def register(self, qAction, actionHandler):
        assert not (qAction in self.__actions), "Given qAction already registered"

        QtCore.QObject.connect(qAction, QtCore.SIGNAL("triggered()"), actionHandler.handle)
        actionHandler.connectSignals(self.__widgetsUpdateManager)

        self.__actions[qAction] = actionHandler

    def unregister(self, qAction):
        assert qAction in self.__actions, "qAction must be registered before"
        actionHandler = self.__actions[qAction]

        actionHandler.disconnectSignals(self.__widgetsUpdateManager)
        QtCore.QObject.disconnect(qAction, QtCore.SIGNAL("triggered()"), actionHandler.handle)

        del self.__actions[qAction]

    def unregisterAll(self):
        for qAction, actionHandler in self.__actions.items():
            actionHandler.disconnectSignals(self.__widgetsUpdateManager)
            QtCore.QObject.disconnect(qAction, QtCore.SIGNAL("triggered()"), actionHandler.handle)

        self.__actions.clear()



class AbstractActionHandler(QtCore.QObject):
    def __init__(self, model=None):
        super(AbstractActionHandler, self).__init__()
        self._gui = model # TODO: remove self._gui as soon as possible from here
        self._tool = model
        self._model = model

    def handle(self):
        raise NotImplementedError("This function should be overriden in subclass")

    def connectSignals(self, widgetsUpdateManager):
        self.connect(self, QtCore.SIGNAL("handlerSignal"), \
                     widgetsUpdateManager.onHandlerSignal)
        self.connect(self, QtCore.SIGNAL("handlerSignals"), \
                     widgetsUpdateManager.onHandlerSignals)

    def disconnectSignals(self, widgetsUpdateManager):
        self.disconnect(self, QtCore.SIGNAL("handlerSignal"), \
                     widgetsUpdateManager.onHandlerSignal)
        self.disconnect(self, QtCore.SIGNAL("handlerSignals"), \
                     widgetsUpdateManager.onHandlerSignals)

    def _emitHandlerSignal(self, handlerSignalType, *params):
        self.emit(QtCore.SIGNAL("handlerSignal"), handlerSignalType, *params)

    def _emitHandlerSignals(self, handlerSignalTypes):
        self.emit(QtCore.SIGNAL("handlerSignals"), handlerSignalTypes)
