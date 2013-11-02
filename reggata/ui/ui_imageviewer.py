# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\imageviewer.ui'
#
# Created: Tue Oct 29 20:36:08 2013
#      by: PyQt4 UI code generator 4.10
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_ImageViewer(object):
    def setupUi(self, ImageViewer):
        ImageViewer.setObjectName(_fromUtf8("ImageViewer"))
        ImageViewer.resize(562, 407)
        self.centralwidget = QtGui.QWidget(ImageViewer)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        ImageViewer.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(ImageViewer)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 562, 26))
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
        ImageViewer.setWindowTitle(_translate("ImageViewer", "ImageViewer", None))
        self.toolBar.setWindowTitle(_translate("ImageViewer", "ImageViewer", None))
        self.action_prev.setText(_translate("ImageViewer", "Previous", None))
        self.action_next.setText(_translate("ImageViewer", "Next", None))
        self.action_zoom_in.setText(_translate("ImageViewer", "Zoom In", None))
        self.action_zoom_out.setText(_translate("ImageViewer", "Zoom Out", None))
        self.action_fit_window.setText(_translate("ImageViewer", "Fit Window", None))
        self.action_edit_item.setText(_translate("ImageViewer", "Edit Item", None))
        self.action_edit_item.setToolTip(_translate("ImageViewer", "Edit Item", None))
        self.action_edit_item.setShortcut(_translate("ImageViewer", "Ctrl+E", None))

from . import resources_rc
