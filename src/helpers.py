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
import consts

logger = logging.getLogger(consts.ROOT_LOGGER + "." + __name__)


#def tr(text):
#    '''Translates text of GUI to foreign languages.'''
#    s = QCoreApplication.translate("@default", str(text), None, QCoreApplication.UnicodeUTF8)
#    return s

class MyMessageBox(QtGui.QMessageBox):
    '''This MessageBox window can be resized with a mouse. Standard QMessageBox
    could not. Solution was taken from here: 
    http://stackoverflow.com/questions/2655354/how-to-allow-resizing-of-qmessagebox-in-pyqt4
    '''
    def __init__(self, parent=None):
        super(MyMessageBox, self).__init__(parent)    
        self.setSizeGripEnabled(True)            
        #Пока что кнопок еще нет. Они добавятся конечно, когда будет вызван setText(), но пока что их нет
        self.addButton(QtGui.QMessageBox.Ok)
        self.setDefaultButton(QtGui.QMessageBox.Ok)
        self.setEscapeButton(QtGui.QMessageBox.Ok)

    def event(self, e):
        result = QtGui.QMessageBox.event(self, e)

        self.setMinimumHeight(0)
        self.setMaximumHeight(16777215)
        self.setMinimumWidth(0)
        self.setMaximumWidth(16777215)
        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

        textEdit = self.findChild(QtGui.QTextEdit)
        if textEdit != None :
            textEdit.setMinimumHeight(0)
            textEdit.setMaximumHeight(16777215)
            textEdit.setMinimumWidth(0)
            textEdit.setMaximumWidth(16777215)
            textEdit.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
            
        return result

def show_exc_info(parent, ex, tracebk=True, details=None, title=None):
    '''
    Если traceback задать равным False, то окно не содержит раздел DetailedText
    с информацией о stack trace (как это по русски сказать?).
    
    Если задать details, то данный текст выводится в разделе DetailedText, причем
    неважно чему при этом равен tracebk (он игнорируется).
    
    Параметр title позволяет задать другой заголовок окна.
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
    
def format_exc_info(type, value, tb):    
    return ''.join(traceback.format_exception(type, value, tb))

#Deprecated: every dialog class should use it's own enumeration of modes!
class DialogMode(object):
    CREATE = 0
    EDIT = 1
    VIEW = 2
    LOGIN = 3

def to_db_format(path):
    '''Преобразует путь path из формата данной ОС в формат UNIX (в котором хранятся
    пути в БД.'''
    if platform.system() == "Windows":
        return path.replace(os.sep, "/")
    else:
        #В случае Linux или Mac OS преобразовывать не нужно
        return path
    
def from_db_format(path):
    '''Преобразует путь path из формата UNIX (в данном формате все пути хранятся в БД) 
    в формат, принятый на конкретной ОС. path должен быть относительным путем. 
    Вобщем-то заменяются только слеши: / на \
    '''
    if platform.system() == "Windows":
        #TODO Перед сохранением файла, необходимо запрещать, чтобы файл содержал 
        #в своем ИМЕНИ символ обратного слеша. Иначе будут проблемы под Windows.
        return path.replace("/", os.sep)
    else:
        #В случае Linux или Mac OS преобразовывать не нужно
        return path

def to_os_format(path):
    return from_db_format(path)
    
    
def to_commalist(seq, apply_each=repr, sep=", "):
    '''
    Для последовательности seq (например, списка list) возвращает строку, содержащую
    элементы через запятую. При этому к каждому элементу применяется функция apply_each()
    для возможно необходимых преобразований формата элементов.
    
    В качестве seq можно также передавать множество set.
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
    '''Возвращает индекс первого найденного элемента из последовательности 
    seq. Для каждого элемента применяется функция match(seq[i]), 
    если match() возвращает True, то элемент найден.    
    Если элемент не найден, то возвращается None.    
    '''
    for i in range(len(seq)):
        if match(seq[i]):    
            return i
    return None
        
def is_none_or_empty(s):
    '''Возвращает True, если строка s является None или "".
    Если передать объект класса, отличного от str, генерируется исключение TypeError.
    '''
    if s is None:
        return True
    else:    
        if not isinstance(s, str):
            raise TypeError("is_none_or_empty() can be applied only to str objects.")    
        return True if s == "" else False

#TODO: Rename into isInternalPath() or isSubDirectoryOf() or isSubPathOf()
def is_internal(url, base_path):
        '''Returns True if url is a path to subdirectory inside base_path directory, else False.
        Method doesn't check existence of tested paths.
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
        
def compute_hash(filename, chunksize=131072, algorithm="sha1"):
    '''Возвращает хэш от содержимого файла filename.'''
    #Можно использовать md5, он вычисляется существенно быстрее, чем sha1.    
    start = time.time()
    f = open(filename, 'rb')
    filehash = hashlib.new(algorithm)
    while True:
        data = f.read(chunksize)
        if not data:
            break
        filehash.update(data)
    hash = filehash.hexdigest()
    logger.debug("Hash {} computed in time of {} sec".format(algorithm, time.time() - start))
    return hash
    
def computePasswordHash(strPassword):
    bytes = strPassword.encode("utf-8")
    return hashlib.sha1(bytes).hexdigest()
    
        
class ImageThumbDelegate(QtGui.QStyledItemDelegate):
    '''Делегат, для отображения миниатюры графического файла в таблице элементов
    хранилища.'''
    def __init__(self, parent=None):
        super(ImageThumbDelegate, self).__init__(parent)
        
    def sizeHint(self, option, index):
        pixmap = index.data(QtCore.Qt.UserRole)
        if pixmap:
            return pixmap.size()
        else:
            return super(ImageThumbDelegate, self).sizeHint(option, index) #Работает в PyQt начиная с 4.8.1            
            

    def paint(self, painter, option, index):
        
        pixmap = index.data(QtCore.Qt.UserRole)
        if pixmap is not None and not pixmap.isNull():
            painter.drawPixmap(option.rect.topLeft(), pixmap)
            #painter.drawPixmap(option.rect, pixmap)
        else:
            super(ImageThumbDelegate, self).paint(painter, option, index) #Работает в PyQt начиная с 4.8.1
            #QtGui.QStyledItemDelegate.paint(self, painter, option, index) #Для PyQt 4.7.3 надо так

class RatingDelegate(QtGui.QStyledItemDelegate):
    '''An ItemDelegate for displaying Rating of items. Rating value is stored 
    in a regular field with name consts.RATING_FIELD.'''
    
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
                path.moveTo(QtCore.QPointF(radius*math.cos(i*2*math.pi/10), radius*math.sin(i*2*math.pi/10)))
            else:
                path.lineTo(QtCore.QPointF(radius*math.cos(i*2*math.pi/10), radius*math.sin(i*2*math.pi/10)))        
        painter.save()
        painter.translate(r, r)
        painter.setPen(palette.text().color())
        painter.setBrush(QtGui.QBrush(palette.button().color()))
        painter.drawPath(path)
        painter.restore()
        
        
        
    
    def sizeHint(self, option, index):
        return QtCore.QSize(option.rect.width(), self.r)
        #TODO should return some size?..
        #return super(RatingDelegate, self).sizeHint(option, index)
            

    def paint(self, painter, option, index):
        
        palette = QtGui.QApplication.palette()
        
        bg_color = palette.highlight().color() \
            if option.state & QtGui.QStyle.State_Selected \
            else palette.base().color()
        
        rating = int(index.data(QtCore.Qt.DisplayRole))
        
        #TODO Maybe max rating should be 10?
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
    '''Делегат, для отображения HTML текста в таблице.'''
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
            return super(HTMLDelegate, self).sizeHint(option, index) #Работает в PyQt начиная с 4.8.1
            

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
            super(HTMLDelegate, self).paint(painter, option, index) #Работает в PyQt начиная с 4.8.1
            

        
        
        