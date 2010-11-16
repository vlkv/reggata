# -*- coding: utf-8 -*-
'''
Created on 04.10.2010

@author: vlkv

Модуль, содержащий различные вспомогательные глобальные функции.

Содержит функцию tr() для более удобного вызова QCoreApplication.translate().
А функции Object.tr() рекомендуется в PyQt не использовать вообще.
'''
from PyQt4.QtCore import (QCoreApplication)
import PyQt4.QtGui as QtGui
import traceback
import os
import hashlib
import time


def tr(text):
    '''Переводит текст сообщений GUI на различные языки.'''

#    print("context={}, text={}".format(context, text))
    s = QCoreApplication.translate("@default", str(text), None, QCoreApplication.UnicodeUTF8)
    return s


def showExcInfo(parent, ex):
    
    '''Окно данного класса можно растягивать мышкой, 
    в отличие от стандартного QMessageBox-а.
    Решение взято отсюда: http://stackoverflow.com/questions/2655354/how-to-allow-resizing-of-qmessagebox-in-pyqt4'''
    class MyMessageBox(QtGui.QMessageBox):
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
    
    mb = MyMessageBox(parent)
    mb.setWindowTitle(tr("Information"))
    mb.setText(str(ex))
    mb.setDetailedText(traceback.format_exc())    
    mb.exec_()
    
    

class DialogMode(object):
    CREATE = 0
    EDIT = 1
    VIEW = 2
    LOGIN = 3
    
    
def to_commalist(seq, apply_each=repr, sep=","):
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
            s = s + sep
    return s
        
def scale_value(value, src_range, dst_range):
    ''' Выполняет масштабирование значения value, которое может варьироваться в пределах
    от src_range[0] до src_range[1], после чего значение попадает в диапазон от dst_range[0] до 
    dst_range[1].
        Если value находится вне диапазона src_range, то оно будет сдвинуто на соответствующую
        границу.
    '''    
    if src_range[0] > src_range[1]:
        raise ValueError(tr("Incorrect range, src_range[0] must be less then src_range[1]."))
    
    if dst_range[0] > dst_range[1]:
        raise ValueError(tr("Incorrect range, dst_range[0] must be less then dst_range[1]."))
    
    result = float(value) * (float(dst_range[0]) - dst_range[1]) / (src_range[0] - src_range[1])
    if result < dst_range[0]:
        result = dst_range[0]
    elif result > dst_range[1]:
        result = dst_range[1]
    return result
        
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
            raise TypeError(tr("is_none_or_empty() can be applied only to str objects."))    
        return True if s == "" else False

def is_internal(url, base_path):
        '''Метод проверяет, находится ли путь url внутри директории base_path или нет.'''
        com_pref = os.path.commonprefix([base_path, url])
        if com_pref == base_path:
            return True
        else:
            return False
        
        
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
    print("Hash {} computed in time of {} sec".format(algorithm, time.time() - start))
    return hash
    
    

        
        
        