# -*- coding: utf-8 -*-
'''
Created on 04.10.2010
@author: vlkv

Module contains various helper global functions.
'''
import PyQt4.QtGui as QtGui
import PyQt4.QtCore as QtCore
from PyQt4.QtCore import Qt
from PyQt4.QtCore import QCoreApplication
import traceback
import os
import hashlib
import time
import platform
import math
import logging
import reggata.consts
from reggata.gui.my_message_box import MyMessageBox

logger = logging.getLogger(reggata.consts.ROOT_LOGGER + "." + __name__)


#def tr(text):
#    '''Translates text of GUI to foreign languages.'''
#    s = QCoreApplication.translate("@default", str(text), None, QCoreApplication.UnicodeUTF8)
#    return s


# TODO: move this function to DialogsFacade
# TODO: split this function to several functions with less arguments...
def show_exc_info(parent, ex, tracebk=True, details=None, title=None):
    '''
        Shows a MyMessageBox dialog with information about given exception.
        parent --- Qt parent of the dialog to be shown.
        ex --- an exception to be described in the dialog.
        tracebk --- when tracebk is True the dialog would contain a DetailedText
    button. When user presses that button --- an info with stack trace is shown in 
    the dialog. 
        details --- when details is not None, then it is displayed in the DetailedText
    area of the dialog (instead of stack trace). In this case value of tracebk is 
    ignored. 
        title --- set different title to the dialog. When title is None, the dialog
    has a default title. 
    '''
    mb = MyMessageBox(parent)
    defaultTitle = QCoreApplication.translate("helpers", "Information", 
                                              None, QCoreApplication.UnicodeUTF8)
    mb.setWindowTitle(defaultTitle if title is None else title)
    mb.setText(str(ex))
    if not is_none_or_empty(details):
        mb.setDetailedText(details)
    elif tracebk:
        mb.setDetailedText(traceback.format_exc())
    
    mb.exec_()
    
    
def format_exc_info(excType, value, tb):    
    return ''.join(traceback.format_exception(excType, value, tb))


def to_db_format(path):
    '''
        Converts slashes of the given path from current OS format to UNIX format. 
    Note: all paths in reggata database are stored in UNIX format.
    '''
    if platform.system() == "Windows":
        return path.replace(os.sep, "/")
    else:
        # Linux and MacOS use UNIX format
        return path

    
def from_db_format(path):
    '''
        Converts slashes of the given path from UNIX format (this format is used
    in reggata database) to the format of the current OS. Path should be a relative path. 
    '''
    if platform.system() == "Windows":
        return path.replace("/", os.sep)
    else:
        # Linux and MacOS use UNIX format
        return path

def to_os_format(path):
    return from_db_format(path)
    
    
def to_commalist(seq, apply_each=repr, sep=", "):
    '''
        For any sequence (e.g. list) this function returns a string, containing
    all elements, separated with commas (by default). When constructing the result
    string, all sequence elements are converted with apply_each function call.
    '''
    s = ""
    i = 0
    for item in seq:
        s = s + apply_each(item)
        if i != len(seq) - 1:
            s = s + sep
        i += 1
    return s
        

def index_of(seq, match=None):
    '''
        Returns an index of the first matching element in sequence. Matching is performed
    with a match callable which should return boolean. Returns None, if there are no 
    matching elements in the sequence.    
    '''
    for i in range(len(seq)):
        if match(seq[i]):    
            return i
    return None
        
        
def is_none_or_empty(s):
    '''
        Returns True, if given string s is None or "" (empty string).
    If s is and instance of class different from str, function raises TypeError.
    '''
    if s is None:
        return True
    else:    
        if not isinstance(s, str):
            raise TypeError("is_none_or_empty() can be applied only to str objects.")    
        return True if s == "" else False


#TODO: Rename into isInternalPath() or isSubDirectoryOf() or isSubPathOf()
def is_internal(url, base_path):
        '''
            Returns True if url is a path to subdirectory inside base_path directory, 
        else False. Method doesn't check existence of tested paths.
        '''
        if is_none_or_empty(base_path):
            raise ValueError("base_path cannot be empty.")
        
        url = os.path.normpath(url)
        base_path = os.path.normpath(base_path)
        com_pref = os.path.commonprefix([base_path, url])
        if com_pref == base_path:
            return True
        else:
            return False


def removeTrailingOsSeps(path):
    while path.endswith(os.sep):
        path = path[0:len(path)-1]
    return path

        
def computeFileHash(filename, chunksize=128*1024): # chunksize = 128 Kbytes 
    '''
        The function calculates hash of a contents of a given file.
    '''
    algorithm = "sha1"
    
    if (os.path.getsize(filename) <= consts.MAX_FILE_SIZE_FOR_FULL_HASHING):
        hashStr = _computeFullFileHash(filename, chunksize, algorithm)
    else:
        hashStr = _computePartialFileHash(
                                          filename, chunksize, algorithm, 
                                          consts.MAX_BYTES_FOR_PARTIAL_HASHING)
        hashStr = "0.." + str(consts.MAX_BYTES_FOR_PARTIAL_HASHING) + ": " + hashStr
    return hashStr

def _computeFullFileHash(filename, chunksize, algorithm):
    assert chunksize > 0
    f = open(filename, 'rb')
    filehash = hashlib.new(algorithm)
    while True:
        data = f.read(chunksize)
        if not data:
            break
        filehash.update(data)
    hashStr = filehash.hexdigest()
    return hashStr    

def _computePartialFileHash(filename, chunksize, algorithm, maxBytesToHash):
    assert chunksize > 0
    assert maxBytesToHash > 0
    assert maxBytesToHash < os.path.getsize(filename)
    
    f = open(filename, 'rb')
    filehash = hashlib.new(algorithm)
    
    while maxBytesToHash > 0:
        bytesToRead = chunksize if maxBytesToHash >= chunksize else maxBytesToHash
        maxBytesToHash -= bytesToRead 
        data = f.read(bytesToRead)
        if not data:
            break
        filehash.update(data)
    hashStr = filehash.hexdigest()
    return hashStr
    
    
def computePasswordHash(strPassword):
    byteData = strPassword.encode("utf-8")
    return hashlib.sha1(byteData).hexdigest()
    
        
class ImageThumbDelegate(QtGui.QStyledItemDelegate):
    '''
        This is an ItemDelegate for rendering an image thumbnail in Items Table Tool.
    '''
    def __init__(self, parent=None):
        super(ImageThumbDelegate, self).__init__(parent)
        
    def sizeHint(self, option, index):
        pixmap = index.data(QtCore.Qt.UserRole)
        if pixmap is not None and not pixmap.isNull():
            return pixmap.size()
        else:
            return super(ImageThumbDelegate, self).sizeHint(option, index)
            
    def paint(self, painter, option, index):
        pixmap = index.data(QtCore.Qt.UserRole)
        if pixmap is not None and not pixmap.isNull():
            painter.drawPixmap(option.rect.topLeft(), pixmap)
        else:
            super(ImageThumbDelegate, self).paint(painter, option, index)


class RatingDelegate(QtGui.QStyledItemDelegate):
    '''
        An ItemDelegate for displaying Rating of items. Rating value is stored 
    in a regular field with name consts.RATING_FIELD.
    '''
    def __init__(self, parent=None, r=10):
        super(RatingDelegate, self).__init__(parent)
        
        palette = QtGui.QApplication.palette()
        
        self.r = r
        self.star = QtGui.QPixmap(2*r, 2*r)
        self.star.fill(QtGui.QColor(255, 255, 255, 0)) #This is an absolutely transparent color
        painter = QtGui.QPainter(self.star)
        path = QtGui.QPainterPath()    
        
        for i in range(0, 10):
            radius = r if i % 2 == 0 else r*0.4
            if i == 0:
                path.moveTo(QtCore.QPointF(radius*math.cos(i*2*math.pi/10), 
                                           radius*math.sin(i*2*math.pi/10)))
            else:
                path.lineTo(QtCore.QPointF(radius*math.cos(i*2*math.pi/10), 
                                           radius*math.sin(i*2*math.pi/10)))        
        painter.save()
        painter.translate(r, r)
        painter.setPen(palette.text().color())
        painter.setBrush(QtGui.QBrush(palette.button().color()))
        painter.drawPath(path)
        painter.restore()
        
    def sizeHint(self, option, index):
        return QtCore.QSize(option.rect.width(), self.r)
        
    def paint(self, painter, option, index):
        palette = QtGui.QApplication.palette()
        
        bg_color = palette.highlight().color() \
            if option.state & QtGui.QStyle.State_Selected \
            else palette.base().color()
        
        rating = int(index.data(QtCore.Qt.DisplayRole))
        
        if rating < 0:
            rating = 0
        elif rating > 5:
            rating = 5
            
        painter.save()
        painter.fillRect(option.rect, bg_color)
        painter.translate(option.rect.x(), option.rect.y())
        for i in range(0, rating):
            painter.drawPixmap(0, 0, self.star)
            painter.translate(self.star.width() + 1, 0.0)
        painter.restore()
        
    def createEditor(self, parent, option, index):
        editor = QtGui.QSpinBox(parent)
        editor.setMinimum(0)
        editor.setMaximum(5)
        return editor
    
    def setEditorData(self, editor, index):
        try:
            rating = int(index.data(QtCore.Qt.DisplayRole))
        except:
            rating = 0
        editor.setValue(rating)
    
    def setModelData(self, editor, model, index):
        model.setData(index, editor.value())
    
    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class HTMLDelegate(QtGui.QStyledItemDelegate):
    '''
        An ItemDelegate for rendering HTML text in Items Table Tool.
    '''
    def __init__(self, parent=None):
        super(HTMLDelegate, self).__init__(parent)
        self.text_edit = QtGui.QTextEdit()
        
    def sizeHint(self, option, index):
        raw_text = index.data(Qt.DisplayRole)
        if raw_text is not None:
            doc = QtGui.QTextDocument()
            doc.setTextWidth(option.rect.width())
            doc.setDefaultFont(option.font)
            doc.setHtml(raw_text)            
            return QtCore.QSize(doc.size().width(), doc.size().height())
        else:
            return super(HTMLDelegate, self).sizeHint(option, index)
            
    def paint(self, painter, option, index):
        palette = QtGui.QApplication.palette()
        
        bg_color = palette.highlight().color() \
            if option.state & QtGui.QStyle.State_Selected \
            else palette.base().color()
            
        text_color = palette.highlightedText().color() \
            if option.state & QtGui.QStyle.State_Selected \
            else palette.text().color()
        
        raw_text = index.data(Qt.DisplayRole)
        if raw_text is not None:
            doc = QtGui.QTextDocument()
            doc.setTextWidth(option.rect.width())
            doc.setDefaultFont(option.font)
            doc.setHtml(raw_text)
            
            cursor = QtGui.QTextCursor(doc)
            format = QtGui.QTextCharFormat()
            format.setForeground(QtGui.QBrush(text_color))
            cursor.movePosition(QtGui.QTextCursor.Start)
            cursor.movePosition(QtGui.QTextCursor.End, QtGui.QTextCursor.KeepAnchor)
            cursor.mergeCharFormat(format)
                    
            painter.save()
            painter.fillRect(option.rect, bg_color)
            painter.translate(option.rect.x(), option.rect.y())
            doc.drawContents(painter, QtCore.QRectF(0 ,0, option.rect.width(), option.rect.height()))            
            painter.restore()
    
        else:
            super(HTMLDelegate, self).paint(painter, option, index)
            

        
        
        