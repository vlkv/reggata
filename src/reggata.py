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

Created on 21.01.2012

@author: vlkv
'''
import os.path
import sys
import datetime
import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui
from PyQt4.QtCore import Qt
import consts
from user_config import UserConfig
from main_window import MainWindow


if __name__ == '__main__':
    if not os.path.exists(consts.DEFAULT_TMP_DIR):
        os.makedirs(consts.DEFAULT_TMP_DIR)
    
    if UserConfig().get("redirect_stdout", "True") in ["True", "true", "TRUE", "1"]:
        sys.stdout = open(os.path.join(consts.DEFAULT_TMP_DIR, "stdout.txt"), "a+")
        
    if UserConfig().get("redirect_stderr", "True") in ["True", "true", "TRUE", "1"]:
        sys.stderr = open(os.path.join(consts.DEFAULT_TMP_DIR, "stderr.txt"), "a+")
    
    print()
    print("========= Reggata started at {} =========".format(datetime.datetime.now()))
    print("pyqt_version = {}".format(QtCore.PYQT_VERSION_STR))
    print("qt_version = {}".format(QtCore.QT_VERSION_STR))
    
    app = QtGui.QApplication(sys.argv)
        
    qtr = QtCore.QTranslator()
    language = UserConfig().get("language")
    if language:
        qm_filename = "reggata_{}.qm".format(language)
        if qtr.load(qm_filename, ".") or qtr.load(qm_filename, ".."):
            app.installTranslator(qtr)
        else:
            print("Cannot find translation file {}.".format(qm_filename))
    
    form = MainWindow()
    form.show()
    app.exec_()


