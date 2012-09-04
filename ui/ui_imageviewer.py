# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'imageviewer.ui'
#
# Created: Tue Sep  4 22:07:08 2012
#      by: PyQt4 UI code generator 4.9.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_ImageViewer(object):
    def setupUi(self, ImageViewer):
        ImageViewer.setObjectName(_fromUtf8("ImageViewer"))
        ImageViewer.resize(562, 407)
        self.centralwidget = QtGui.QWidget(ImageViewer)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        ImageViewer.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(ImageViewer)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 562, 22))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        ImageViewer.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(ImageViewer)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        ImageViewer.setStatusBar(self.statusbar)
        self.toolBar = QtGui.QToolBar(ImageViewer)
        self.toolBar.setObjectName(_fromUtf8("toolBar"))
        ImageViewer.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.action_prev = QtGui.QAction(ImageViewer)
        self.action_prev.setEnabled(True)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/icons/go-previous.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.action_prev.setIcon(icon)
        self.action_prev.setVisible(True)
        self.action_prev.setIconVisibleInMenu(True)
        self.action_prev.setObjectName(_fromUtf8("action_prev"))
        self.action_next = QtGui.QAction(ImageViewer)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/icons/go-next.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.action_next.setIcon(icon1)
        self.action_next.setObjectName(_fromUtf8("action_next"))
        self.action_zoom_in = QtGui.QAction(ImageViewer)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/icons/zoom_in.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.action_zoom_in.setIcon(icon2)
        self.action_zoom_in.setObjectName(_fromUtf8("action_zoom_in"))
        self.action_zoom_out = QtGui.QAction(ImageViewer)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/icons/zoom_out.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.action_zoom_out.setIcon(icon3)
        self.action_zoom_out.setObjectName(_fromUtf8("action_zoom_out"))
        self.action_fit_window = QtGui.QAction(ImageViewer)
        self.action_fit_window.setCheckable(True)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/icons/fit_window.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.action_fit_window.setIcon(icon4)
        self.action_fit_window.setObjectName(_fromUtf8("action_fit_window"))
        self.action_edit_item = QtGui.QAction(ImageViewer)
        self.action_edit_item.setObjectName(_fromUtf8("action_edit_item"))
        self.toolBar.addAction(self.action_prev)
        self.toolBar.addAction(self.action_next)
        self.toolBar.addAction(self.action_zoom_in)
        self.toolBar.addAction(self.action_zoom_out)
        self.toolBar.addAction(self.action_fit_window)
        self.toolBar.addAction(self.action_edit_item)

        self.retranslateUi(ImageViewer)
        QtCore.QMetaObject.connectSlotsByName(ImageViewer)

    def retranslateUi(self, ImageViewer):
        ImageViewer.setWindowTitle(QtGui.QApplication.translate("ImageViewer", "ImageViewer", None, QtGui.QApplication.UnicodeUTF8))
        self.toolBar.setWindowTitle(QtGui.QApplication.translate("ImageViewer", "ImageViewer", None, QtGui.QApplication.UnicodeUTF8))
        self.action_prev.setText(QtGui.QApplication.translate("ImageViewer", "Previous", None, QtGui.QApplication.UnicodeUTF8))
        self.action_next.setText(QtGui.QApplication.translate("ImageViewer", "Next", None, QtGui.QApplication.UnicodeUTF8))
        self.action_zoom_in.setText(QtGui.QApplication.translate("ImageViewer", "Zoom In", None, QtGui.QApplication.UnicodeUTF8))
        self.action_zoom_out.setText(QtGui.QApplication.translate("ImageViewer", "Zoom Out", None, QtGui.QApplication.UnicodeUTF8))
        self.action_fit_window.setText(QtGui.QApplication.translate("ImageViewer", "Fit Window", None, QtGui.QApplication.UnicodeUTF8))
        self.action_edit_item.setText(QtGui.QApplication.translate("ImageViewer", "Edit Item", None, QtGui.QApplication.UnicodeUTF8))
        self.action_edit_item.setToolTip(QtGui.QApplication.translate("ImageViewer", "Edit Item", None, QtGui.QApplication.UnicodeUTF8))
        self.action_edit_item.setShortcut(QtGui.QApplication.translate("ImageViewer", "Ctrl+E", None, QtGui.QApplication.UnicodeUTF8))

import resources_rc
