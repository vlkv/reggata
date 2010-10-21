# -*- coding: utf-8 -*-
'''
Created on 04.10.2010

@author: vlkv

Содержит функцию tr() для более удобного вызова QCoreApplication.translate().
А функции Object.tr() рекомендуется в PyQt не использовать вообще.
'''
from PyQt4.QtCore import (QCoreApplication)
import PyQt4.QtGui as QtGui
import traceback


def tr(text, context="default"):
    '''Переводит текст сообщений GUI на различные языки.'''
    return QCoreApplication.translate(context, str(text), None, QCoreApplication.UnicodeUTF8)


def showExcInfo(parent, ex):
    
    '''Окно данного класса можно растягивать мышкой, 
    в отличие от стандартного QMessageBox-а.
    Решение взято отсюда: http://stackoverflow.com/questions/2655354/how-to-allow-resizing-of-qmessagebox-in-pyqt4'''
    class MyMessageBox(QtGui.QMessageBox):
        def __init__(self, parent=None):
            super(MyMessageBox, self).__init__(parent)    
            self.setSizeGripEnabled(True)
    
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
    
    mb = MyMessageBox(parent)
    mb.setWindowTitle(tr("Ошибка"))
    mb.setText(str(ex))
    mb.setDetailedText(traceback.format_exc())
    mb.exec_()
    
    

class DialogMode(object):
    CREATE = 0
    EDIT = 1
    VIEW = 2
    LOGIN = 3
    
    
def to_commalist(seq, apply_each=repr):
    '''
    Для последовательности seq (например, списка list) возвращает строку, содержащую
    элементы через запятую. При этому к каждому элементу применяется функция apply_each()
    для возможно необходимых преобразований формата элементов.
    '''
    s = ""
    for i in range(len(seq)):
        item = seq[i]
        s = s + apply_each(item)
        if i != len(seq) - 1:
            s = s + ','        
    return s
        
        