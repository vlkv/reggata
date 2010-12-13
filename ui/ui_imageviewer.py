# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'imageviewer.ui'
#
# Created: Mon Dec 13 12:20:31 2010
#      by: PyQt4 UI code generator 4.8.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(562, 407)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 562, 26))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)
        self.toolBar = QtGui.QToolBar(MainWindow)
        self.toolBar.setObjectName(_fromUtf8("toolBar"))
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.action_prev = QtGui.QAction(MainWindow)
        self.action_prev.setEnabled(True)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("../../../images/icons/tango-icon-theme-0.8.90/22x22/actions/go-previous.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.action_prev.setIcon(icon)
        self.action_prev.setVisible(True)
        self.action_prev.setIconVisibleInMenu(True)
        self.action_prev.setObjectName(_fromUtf8("action_prev"))
        self.action_next = QtGui.QAction(MainWindow)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8("../../../images/icons/tango-icon-theme-0.8.90/22x22/actions/go-next.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.action_next.setIcon(icon1)
        self.action_next.setObjectName(_fromUtf8("action_next"))
        self.toolBar.addAction(self.action_prev)
        self.toolBar.addAction(self.action_next)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.toolBar.setWindowTitle(QtGui.QApplication.translate("MainWindow", "ImageViewer", None, QtGui.QApplication.UnicodeUTF8))
        self.action_prev.setText(QtGui.QApplication.translate("MainWindow", "Previous", None, QtGui.QApplication.UnicodeUTF8))
        self.action_next.setText(QtGui.QApplication.translate("MainWindow", "Next", None, QtGui.QApplication.UnicodeUTF8))

