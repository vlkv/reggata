# -*- coding: utf-8 -*-
'''
Created on 04.10.2010

@author: vlkv

Содержит функцию tr() для более удобного вызова QCoreApplication.translate().
А функции Object.tr() рекомендуется в PyQt не использовать вообще.
'''
from PyQt4.QtCore import (QCoreApplication)
import PyQt4.QtGui as qtgui
import traceback

def tr(text, context="default"):
    return QCoreApplication.translate(context, str(text), None, QCoreApplication.UnicodeUTF8)


def showExcInfo(parent, ex):
    mb = qtgui.QMessageBox(parent)
    mb.setWindowTitle(tr("Ошибка"))
    mb.setText(str(ex))
    mb.setDetailedText(traceback.format_exc())
#    mb.setSizePolicy(qtgui.QSizePolicy.Expanding, qtgui.QSizePolicy.Expanding)
    mb.exec_()
    
    

class DialogMode(object):
    CREATE = 0
    EDIT = 1
    VIEW = 2
    LOGIN = 3
    