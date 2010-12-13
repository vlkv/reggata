# -*- coding: utf-8 -*-
'''
Copyright 2010 Vitaly Volkov

This file is part of Reggata.

Reggata is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Reggata is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Reggata.  If not, see <http://www.gnu.org/licenses/>.

Created on 13.12.2010
'''

from PyQt4.QtCore import Qt
from PyQt4 import QtGui, QtCore
import ui_imageviewer
from helpers import show_exc_info
from exceptions import MsgException

class Canvas(QtGui.QWidget):
    
    def __init__(self, parent=None):
        super(Canvas, self).__init__(parent)
        self.pixmap = QtGui.QPixmap()
        self.scaled = QtGui.QPixmap()
        self._abs_path = None
        self.x = 0
        self.y = 0
        self.setMouseTracking(False)
        self._scale = 1.0
    
    def paintEvent(self, paint_event):

        if self.pixmap.isNull():
            if not self.pixmap.load(self.abs_path):
                #self.ui.statusbar.showMessage(self.tr("Cannot load image {0}.").format(self.abs_paths[self.i_current]))
                return
            
        if self.scaled.isNull() and not self.pixmap.isNull():
            self.scaled = self.pixmap.scaled(int(self.pixmap.width()*self.scale), \
                                             int(self.pixmap.height()*self.scale), \
                                             Qt.KeepAspectRatio)
            
        
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.drawPixmap(self.x, self.y, self.scaled)
        painter.end()

    @property
    def scale(self):
        return self._scale
    
    @scale.setter
    def scale(self, value):
        self._scale = value
        self.scaled = QtGui.QPixmap()

    @property
    def abs_path(self):
        return self._abs_path

    @abs_path.setter
    def abs_path(self, path):
        self._abs_path = path
        self.pixmap = QtGui.QPixmap()
        self.scaled = QtGui.QPixmap()
    
    def mouseMoveEvent(self, ev):
        self.x -= ev.pos().x() - self.press_x
        self.y -= ev.pos().y() - self.press_y        
        if self.x < -self.scaled.width() + self.width():
            self.x = -self.scaled.width() + self.width()
        if self.y < -self.scaled.height() + self.height():
            self.y = -self.scaled.height() + self.height()
        if self.x > 0:
            self.x = 0
        if self.y > 0:
            self.y = 0
        self.update()
        
        
    def mousePressEvent(self, ev):
        self.press_x = ev.pos().x()
        self.press_y = ev.pos().y()
        self.update()
        
    def mouseReleaseEvent(self, ev):
        self.update()
        print("canvas={}x{} scaled={}x{}".format(self.width(), self.height(), self.scaled.width(), self.scaled.height()))
        print("pixmap={}x{}".format(self.pixmap.width(), self.pixmap.height()))
    

class ImageViewer(QtGui.QMainWindow):
    '''
    Встроенный просмотрщик изображений.
    '''


    def __init__(self, parent=None, abs_paths=[]):
        super(ImageViewer, self).__init__(parent)
        self.ui = ui_imageviewer.Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.abs_paths = abs_paths
        self.i_current = 0 if len(self.abs_paths) > 0 else None
        
        self.ui.canvas = Canvas(self)
        self.setCentralWidget(self.ui.canvas)
        if self.i_current is not None:
            self.ui.canvas.abs_path = self.abs_paths[self.i_current]
        
        self.connect(self.ui.action_prev, QtCore.SIGNAL("triggered()"), self.action_prev)
        self.connect(self.ui.action_next, QtCore.SIGNAL("triggered()"), self.action_next)        
        self.connect(self.ui.action_zoom_In, QtCore.SIGNAL("triggered()"), self.action_zoom_in)
        self.connect(self.ui.action_zoom_out, QtCore.SIGNAL("triggered()"), self.action_zoom_out)
        self.connect(self.ui.action_fit_Window, QtCore.SIGNAL("triggered()"), self.action_fit_window)
            
    def action_zoom_in(self):
        try:
            self.ui.canvas.scale = self.ui.canvas.scale*1.5 
            self.update()
        except Exception as ex:
            show_exc_info(self, ex)
    
    def action_zoom_out(self):
        try:
            self.ui.canvas.scale = self.ui.canvas.scale/1.5 
            self.update()
        except Exception as ex:
            show_exc_info(self, ex)
    
    def action_fit_window(self):
        try:
            scale_x = float(self.ui.canvas.width())/self.ui.canvas.pixmap.width() 
            scale_y = float(self.ui.canvas.height())/self.ui.canvas.pixmap.height()
            scale = scale_x if scale_x < scale_y else scale_y
            self.ui.canvas.scale = scale 
            self.update()
        except Exception as ex:
            show_exc_info(self, ex)
    
    def action_next(self):
        try:
            self.i_current += 1
            if self.i_current >= len(self.abs_paths):
                self.i_current = 0
            
            self.ui.canvas.abs_path = self.abs_paths[self.i_current]
            self.update()
            
        except Exception as ex:
            show_exc_info(self, ex)
            
    def action_prev(self):
        try:
            self.i_current -= 1
            if self.i_current < 0:
                self.i_current = len(self.abs_paths) - 1
            
            self.ui.canvas.abs_path = self.abs_paths[self.i_current]            
            self.update()
            
        except Exception as ex:
            show_exc_info(self, ex)
            
            
    def action_template(self):
        try:
            pass
        except Exception as ex:
            show_exc_info(self, ex)
        
        
    