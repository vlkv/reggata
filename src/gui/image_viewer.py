# -*- coding: utf-8 -*-

from PyQt4.QtCore import Qt
from PyQt4 import QtGui, QtCore
import ui_imageviewer
import helpers
from helpers import show_exc_info
from errors import MsgException
from user_config import UserConfig
import logging
import consts
import os
from data.commands import GetExpungedItemCommand, UpdateExistingItemCommand
from gui.user_dialogs_facade import UserDialogsFacade
from gui.item_dialog import ItemDialog
from logic.handler_signals import HandlerSignals

logger = logging.getLogger(consts.ROOT_LOGGER + "." + __name__)

class Canvas(QtGui.QWidget):
    '''
        This is a widget for image rendering. It also provides basic functions 
    of zooming, panoraming and so on.
    '''
    
    def __init__(self, parent=None):
        super(Canvas, self).__init__(parent)
        self.original = QtGui.QPixmap()
        self.scaled = QtGui.QPixmap()
        self._abs_path = None
        self.x = 0
        self.y = 0
        self.setMouseTracking(False)
        self._scale = 1.0
        self._fit_window = True
    
    def _scale_original(self):
        
        if self.original.isNull():
            return
        
        if self.fit_window:
            scale_x = float(self.width())/self.original.width() 
            scale_y = float(self.height())/self.original.height()
            scale = scale_x if scale_x < scale_y else scale_y
            self._scale = scale
            self.scaled = QtGui.QPixmap()
            
        self.scaled = self.original.scaled(int(self.original.width()*self.scale), \
                                             int(self.original.height()*self.scale), \
                                             Qt.KeepAspectRatio)
    
    def paintEvent(self, paint_event):
        if self.abs_path is None:
            return

        if self.original.isNull():
            if not self.original.load(self.abs_path):
                return
            
        if self.scaled.isNull() and not self.original.isNull():
            self._scale_original()
            
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.drawPixmap(self.x, self.y, self.scaled)
        painter.end()

    def zoom_in(self, koeff=1.5):
        self.scale = self.scale * koeff
        self.update()
    
    def zoom_out(self, koeff=1.5):
        self.scale = self.scale / koeff
        self.update()

    @property
    def fit_window(self):
        return self._fit_window
    
    @fit_window.setter
    def fit_window(self, value):
        self._fit_window = value
        if value:
            self.x = 0
            self.y = 0
        self._scale_original()
            

    @property
    def scale(self):
        return self._scale
    
    @scale.setter
    def scale(self, value):
        self._fit_window = False
        self.emit(QtCore.SIGNAL("fit_window_changed"), False)
        self._scale = value
        self._scale_original()

    @property
    def abs_path(self):
        return self._abs_path

    @abs_path.setter
    def abs_path(self, path):
        self._abs_path = path
        self.original = QtGui.QPixmap()
        self.scaled = QtGui.QPixmap()
    
    def mouseMoveEvent(self, ev):
        self.x += (ev.pos().x() - self.press_x)
        self.y += (ev.pos().y() - self.press_y)
        
        self.press_x = ev.pos().x()
        self.press_y = ev.pos().y()
                
        if self.x < -self.scaled.width() + self.width():
            self.x = -self.scaled.width() + self.width()
        if self.y < -self.scaled.height() + self.height():
            self.y = -self.scaled.height() + self.height()
        if self.x > 0:
            self.x = 0
        if self.y > 0:
            self.y = 0
        self.update()        
        
    def resizeEvent(self, ev):
        self._scale_original()
        
    def mousePressEvent(self, ev):
        self.press_x = ev.pos().x()
        self.press_y = ev.pos().y()
        self.update()
        
    def mouseReleaseEvent(self, ev):
        self.update()
        logger.debug("canvas={}x{} scaled={}x{}".format(self.width(), self.height(), self.scaled.width(), self.scaled.height()))
        logger.debug("original={}x{}".format(self.original.width(), self.original.height()))
    

class ImageViewer(QtGui.QMainWindow):
    '''
    This is a built-in Reggata Image Viewer.
    '''

    def __init__(self, parent, widgetsUpdateManager, repo, userLogin, items, startItemIndex=0):
        '''
            parent --- parent of this widget.
            widgetsUpdateManager --- object that would inform other widgets that some 
        Item has changed after edit action.
            items --- a list of items to show.
            startItemIndex --- index of the first item to show. 
             
        be able to edit items.
        '''
        super(ImageViewer, self).__init__(parent)
        self.ui = ui_imageviewer.Ui_ImageViewer()
        self.ui.setupUi(self)
        self.setWindowModality(Qt.WindowModal)
        
        self.__widgetsUpdateManager = widgetsUpdateManager
        self.connect(self, QtCore.SIGNAL("handlerSignal"),
                     self.__widgetsUpdateManager.onHandlerSignal)
        self.connect(self, QtCore.SIGNAL("handlerSignals"),
                     self.__widgetsUpdateManager.onHandlerSignals)
        
        self.items = items
        self.i_current = startItemIndex if 0 <= startItemIndex < len(items) else 0
        self.repo = repo
        self.user_login = userLogin
        
        self.ui.canvas = Canvas(self)
        self.setCentralWidget(self.ui.canvas)
        
        self.__renderCurrentItemFile()
            
        self.connect(self.ui.action_prev, QtCore.SIGNAL("triggered()"), self.action_prev)
        self.connect(self.ui.action_next, QtCore.SIGNAL("triggered()"), self.action_next)        
        self.connect(self.ui.action_zoom_in, QtCore.SIGNAL("triggered()"), self.action_zoom_in)
        self.connect(self.ui.action_zoom_out, QtCore.SIGNAL("triggered()"), self.action_zoom_out)
        self.connect(self.ui.action_fit_window, QtCore.SIGNAL("triggered(bool)"), self.action_fit_window)
        self.ui.action_fit_window.setChecked(self.ui.canvas.fit_window)
        
        self.connect(self.ui.action_edit_item, QtCore.SIGNAL("triggered()"), self.action_edit_item)
        
        self.connect(self.ui.canvas, QtCore.SIGNAL("fit_window_changed"), \
                     lambda x: self.ui.action_fit_window.setChecked(x))
        
        # Trying to restore window size
        try:
            width = int(UserConfig().get("image_viewer.width", 640))
            height = int(UserConfig().get("image_viewer.height", 480))
            self.resize(width, height)
        except:
            pass
        
        # This code stores window size (after window resizing) 
        self.save_state_timer = QtCore.QTimer(self)
        self.save_state_timer.setSingleShot(True)
        self.connect(self.save_state_timer, QtCore.SIGNAL("timeout()"), self.save_window_state)
        
        #Context menu
        self.menu = QtGui.QMenu()
        self.menu.addAction(self.ui.action_edit_item)
        self.ui.canvas.setContextMenuPolicy(Qt.CustomContextMenu)
        self.connect(self.ui.canvas, QtCore.SIGNAL("customContextMenuRequested(const QPoint &)"), \
                     lambda pos: self.menu.exec_(self.ui.canvas.mapToGlobal(pos)))
        
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Plus:
            self.ui.canvas.zoom_in()
        elif event.key() == Qt.Key_Minus:
            self.ui.canvas.zoom_out()
        elif event.key() == Qt.Key_Space or event.key() == Qt.Key_Right:
            self.action_next()
        elif event.key() == Qt.Key_Backspace or event.key() == Qt.Key_Left:
            self.action_prev()
        elif event.key() == Qt.Key_Escape:
            self.close()
        else:
            super(ImageViewer, self).keyPressEvent(event)
        
    def wheelEvent(self, event):
        if event.delta() < 0:
            #scroll down
            self.action_next()
        else:
            #scroll up
            self.action_prev()
    
        
    def save_window_state(self):        
        UserConfig().storeAll({"image_viewer.width":self.width(), "image_viewer.height":self.height()})
                
    
    def resizeEvent(self, resize_event):
        self.save_state_timer.start(3000)        
    
    def action_zoom_in(self):
        try:            
            self.ui.canvas.zoom_in()
        except Exception as ex:
            show_exc_info(self, ex)
    
    def action_zoom_out(self):
        try:
            self.ui.canvas.zoom_out()
        except Exception as ex:
            show_exc_info(self, ex)
    
    def action_fit_window(self, checked):
        try:
            self.ui.canvas.fit_window = checked
            self.update()
        except Exception as ex:
            show_exc_info(self, ex)
    
    def action_next(self):
        try:
            self.i_current += 1
            if self.i_current >= len(self.items):
                self.i_current = 0
            
            self.__renderCurrentItemFile()
            
        except Exception as ex:
            show_exc_info(self, ex)
            
    def action_prev(self):
        try:
            self.i_current -= 1
            if self.i_current < 0:
                self.i_current = len(self.items) - 1
            
            self.__renderCurrentItemFile()
            
        except Exception as ex:
            show_exc_info(self, ex)
            
            
    def __renderCurrentItemFile(self):
        item = self.items[self.i_current]
        if item.data_ref is not None:
            path = os.path.join(self.repo.base_path, item.data_ref.url)
        else:
            path = None
        self.ui.canvas.abs_path = path
        self.update()
        
        message = item.title + ", " + (path if path is not None else self.tr("No file"))        
        self.ui.statusbar.showMessage(message)
        
   
            
    def __checkActiveRepoIsNotNone(self):
        if self.repo is None:
            raise MsgException(self.tr("Cannot edit items, repository is not given."))
    
    def __checkActiveUserIsNotNone(self):
        if helpers.is_none_or_empty(self.user_login):
            raise MsgException(self.tr("Cannot edit items, user is not given."))
            
   
    def action_edit_item(self):
        try:
            self.__checkActiveRepoIsNotNone()
            self.__checkActiveUserIsNotNone()            
            
            itemId = self.items[self.i_current].id
            self.__editSingleItem(itemId)
            
        except Exception as ex:
            show_exc_info(self, ex)
        else:
            # TODO: pass some item id so widgets could update only edited item 
            self.emit(QtCore.SIGNAL("handlerSignal"), HandlerSignals.ITEM_CHANGED)
    
     
    def __editSingleItem(self, itemId):
        uow = self.repo.create_unit_of_work()
        try:
            item = uow.executeCommand(GetExpungedItemCommand(itemId))
            
            dialogs = UserDialogsFacade()
            if not dialogs.execItemDialog(
                item=item, gui=self, dialogMode=ItemDialog.EDIT_MODE):
                self.ui.statusbar.showMessage(self.tr("Operation cancelled."), consts.STATUSBAR_TIMEOUT)
                return
            
            cmd = UpdateExistingItemCommand(item, self.user_login)
            uow.executeCommand(cmd)
            self.ui.statusbar.showMessage(self.tr("Operation completed."), consts.STATUSBAR_TIMEOUT)
        finally:
            uow.close()
            
    # This property is needed for partial compatibility with AbstractGui
    @property
    def active_repo(self):
        return self.repo
    