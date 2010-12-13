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
from user_config import UserConfig

class Canvas(QtGui.QWidget):
    '''
    Виджет, для отображения изображений, с функциями зуммирования, панорамирования и т.п.
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

        if self.original.isNull():
            if not self.original.load(self.abs_path):
                #self.ui.statusbar.showMessage(self.tr("Cannot load image {0}.").format(self.abs_paths[self.i_current]))
                return
            
        if self.scaled.isNull() and not self.original.isNull():
            self._scale_original()
            
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.drawPixmap(self.x, self.y, self.scaled)
        painter.end()

    @property
    def fit_window(self):
        return self._fit_window
    
    @fit_window.setter
    def fit_window(self, value):
        self._fit_window = value
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
        
        #TODO Может тут лучше послать сигнал?
        self.parent().ui.statusbar.showMessage(self._abs_path)
    
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
        print("canvas={}x{} scaled={}x{}".format(self.width(), self.height(), self.scaled.width(), self.scaled.height()))
        print("original={}x{}".format(self.original.width(), self.original.height()))
    

class ImageViewer(QtGui.QMainWindow):
    '''
    Встроенный просмотрщик изображений.
    '''
    #TODO Если вдруг в список файлов, которые нужно отобразить будет содержать 
    #невероятно много элементов, тогда в конструктор можно передавать не список, 
    #а объект, который ведет себя как список, но на самом деле --- выполняет
    #буферизованное чтение информации из БД

    def __init__(self, parent=None, abs_paths=[]):
        super(ImageViewer, self).__init__(parent)
        self.ui = ui_imageviewer.Ui_ImageViewer()
        self.ui.setupUi(self)
        
        self.abs_paths = abs_paths
        self.i_current = 0 if len(self.abs_paths) > 0 else None
        
        self.ui.canvas = Canvas(self)
        self.setCentralWidget(self.ui.canvas)
        self.ui.action_fit_window.setChecked(self.ui.canvas.fit_window)
        if self.i_current is not None:
            self.ui.canvas.abs_path = self.abs_paths[self.i_current]
        
        self.connect(self.ui.action_prev, QtCore.SIGNAL("triggered()"), self.action_prev)
        self.connect(self.ui.action_next, QtCore.SIGNAL("triggered()"), self.action_next)        
        self.connect(self.ui.action_zoom_in, QtCore.SIGNAL("triggered()"), self.action_zoom_in)
        self.connect(self.ui.action_zoom_out, QtCore.SIGNAL("triggered()"), self.action_zoom_out)
        self.connect(self.ui.action_fit_window, QtCore.SIGNAL("triggered(bool)"), self.action_fit_window)
        
        self.connect(self.ui.canvas, QtCore.SIGNAL("fit_window_changed"), lambda x: self.ui.action_fit_window.setChecked(x))
        
        #Пытаемся восстанавливить размер окна, как был при последнем запуске
        try:
            width = int(UserConfig().get("image_viewer.width", 640))
            height = int(UserConfig().get("image_viewer.height", 480))
            self.resize(width, height)
        except:
            pass
        
        #Делаем так, чтобы размер окна сохранялся при изменении
        self.save_state_timer = QtCore.QTimer(self)
        self.save_state_timer.setSingleShot(True)
        self.connect(self.save_state_timer, QtCore.SIGNAL("timeout()"), self.save_window_state)
        
    def save_window_state(self):        
        UserConfig().storeAll({"image_viewer.width":self.width(), "image_viewer.height":self.height()})
                
    
    def resizeEvent(self, resize_event):
        self.save_state_timer.start(3000) #Повторный вызов start() делает перезапуск таймера        
    
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
    
    def action_fit_window(self, checked):
        try:
            self.ui.canvas.fit_window = checked
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
        
        
    