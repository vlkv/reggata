'''
Created on 13.12.2010

@author: vlkv
'''
from PyQt4 import QtGui, QtCore
import ui_imageviewer
from helpers import show_exc_info
from exceptions import MsgException

class Canvas(QtGui.QWidget):
    
    def __init__(self, parent=None):
        super(Canvas, self).__init__(parent)
        self.pixmap = None
        self._abs_path = None
    
    def paintEvent(self, paint_event):
        if self.i_current is None:
            #self.ui.statusbar.showMessage(self.tr("There is no images."))
            return
        
        if self.pixmap is None:
            self.pixmap = QtGui.QPixmap()
            
        if self.pixmap.isNull():            
            if not self.pixmap.load(self.abs_path):
                #self.ui.statusbar.showMessage(self.tr("Cannot load image {0}.").format(self.abs_paths[self.i_current]))
                return
        
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.drawPixmap(0, 0, self.pixmap)
        painter.end()

    @property
    def abs_path(self):
        return self._abs_path

    @abs_path.setter
    def abs_path(self, path):
        self._abs_path = path
    
    

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
        
        self.connect(self.ui.action_prev, QtCore.SIGNAL("triggered()"), self.action_prev)
        self.connect(self.ui.action_next, QtCore.SIGNAL("triggered()"), self.action_next)
        
    
    def show_image(self):        
        try:
            if not self.i_current:
                raise MsgException(self.tr("There is no images."))
            
            pm = QtGui.QPixmap()
            if not pm.load(self.abs_paths[self.i_current]):
                raise MsgException(self.tr("Cannot load image {0}.").format(self.abs_paths[self.i_current]))
            
            #...
            
        except Exception as ex:
            show_exc_info(self, ex)
        
            
    def paintEvent(self, paint_event):
#        try:
        if self.i_current is None:
            self.ui.statusbar.showMessage(self.tr("There is no images."))
            return
        
        pm = QtGui.QPixmap()
        if not pm.load(self.abs_paths[self.i_current]):
            self.ui.statusbar.showMessage(self.tr("Cannot load image {0}.").format(self.abs_paths[self.i_current]))
            return
        
        print(1)
        painter = QtGui.QPainter()
        print(2)
        painter.begin(self)
        print(3)
        painter.drawPixmap(0, 0, pm)
        print(4)
        painter.end()
        print(5)
            
            
#        except Exception as ex:
#            self.ui.statusbar.showMessage(self.tr("Exception {0} is raised. Message: {1}.").format(str(ex.__class__.__name__), str(ex)))
#        else:
#            self.ui.statusbar.showMessage(self.tr("Image {0}").format(str(self.abs_paths[self.i_current])))
#            
            
            
    

    
    
    def action_prev(self):
        try:
            self.i_current += 1
            if self.i_current >= len(self.abs_paths):
                self.i_current = 0
            
            #self.show_image()
#            self.repaint()
            self.update()
            
        except Exception as ex:
            show_exc_info(self, ex)
            
    def action_next(self):
        try:
            self.i_current -= 1
            if self.i_current < 0:
                self.i_current = len(self.abs_paths) - 1
            
            #self.show_image()
#            self.repaint()
            self.update()
            
        except Exception as ex:
            show_exc_info(self, ex)
            
            
    def action_template(self):
        try:
            pass
        except Exception as ex:
            show_exc_info(self, ex)
        
        
    