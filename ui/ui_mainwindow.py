# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mainwindow.ui'
#
# Created: Sat Oct  2 23:15:01 2010
#      by: PyQt4 UI code generator 4.7.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(556, 417)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.pushButton_test = QtGui.QPushButton(self.centralwidget)
        self.pushButton_test.setGeometry(QtCore.QRect(10, 10, 83, 26))
        self.pushButton_test.setObjectName("pushButton_test")
        self.label_test = QtGui.QLabel(self.centralwidget)
        self.label_test.setGeometry(QtCore.QRect(80, 70, 57, 16))
        self.label_test.setObjectName("label_test")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 556, 26))
        self.menubar.setObjectName("menubar")
        self.menu_repo = QtGui.QMenu(self.menubar)
        self.menu_repo.setObjectName("menu_repo")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.action_repo_create = QtGui.QAction(MainWindow)
        self.action_repo_create.setObjectName("action_repo_create")
        self.action_repo_open = QtGui.QAction(MainWindow)
        self.action_repo_open.setObjectName("action_repo_open")
        self.action_repo_close = QtGui.QAction(MainWindow)
        self.action_repo_close.setObjectName("action_repo_close")
        self.action_repo_add_file = QtGui.QAction(MainWindow)
        self.action_repo_add_file.setObjectName("action_repo_add_file")
        self.menu_repo.addAction(self.action_repo_create)
        self.menu_repo.addAction(self.action_repo_open)
        self.menu_repo.addAction(self.action_repo_close)
        self.menu_repo.addAction(self.action_repo_add_file)
        self.menubar.addAction(self.menu_repo.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_test.setText(QtGui.QApplication.translate("MainWindow", "Тест", None, QtGui.QApplication.UnicodeUTF8))
        self.label_test.setText(QtGui.QApplication.translate("MainWindow", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))
        self.menu_repo.setTitle(QtGui.QApplication.translate("MainWindow", "Хранилище", None, QtGui.QApplication.UnicodeUTF8))
        self.action_repo_create.setText(QtGui.QApplication.translate("MainWindow", "Создать", None, QtGui.QApplication.UnicodeUTF8))
        self.action_repo_open.setText(QtGui.QApplication.translate("MainWindow", "Открыть", None, QtGui.QApplication.UnicodeUTF8))
        self.action_repo_close.setText(QtGui.QApplication.translate("MainWindow", "Закрыть", None, QtGui.QApplication.UnicodeUTF8))
        self.action_repo_add_file.setText(QtGui.QApplication.translate("MainWindow", "Добавить файл", None, QtGui.QApplication.UnicodeUTF8))

