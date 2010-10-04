# -*- coding: utf-8 -*-
'''
Created on 04.10.2010

@author: vlkv

Содержит функцию tr() для более удобного вызова QCoreApplication.translate().
А функции Object.tr() рекомендуется в PyQt не использовать вообще.
'''
from PyQt4.QtCore import (QCoreApplication, QTextCodec)


def tr(text, context="default"):
    return QCoreApplication.translate(context, str(text))
