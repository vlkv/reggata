# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mainwindow.ui'
#
# Created: Sun Oct 17 21:04:52 2010
#      by: PyQt4 UI code generator 4.7.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(678, 432)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 678, 26))
        self.menubar.setObjectName("menubar")
        self.menu_repo = QtGui.QMenu(self.menubar)
        self.menu_repo.setObjectName("menu_repo")
        self.menu = QtGui.QMenu(self.menubar)
        self.menu.setObjectName("menu")
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
        self.action_repo_add_item = QtGui.QAction(MainWindow)
        self.action_repo_add_item.setObjectName("action_repo_add_item")
        self.action_user_create = QtGui.QAction(MainWindow)
        self.action_user_create.setObjectName("action_user_create")
        self.action_user_login = QtGui.QAction(MainWindow)
        self.action_user_login.setObjectName("action_user_login")
        self.action_user_logout = QtGui.QAction(MainWindow)
        self.action_user_logout.setObjectName("action_user_logout")
        self.menu_repo.addAction(self.action_repo_create)
        self.menu_repo.addAction(self.action_repo_open)
        self.menu_repo.addAction(self.action_repo_close)
        self.menu_repo.addAction(self.action_repo_add_item)
        self.menu.addAction(self.action_user_create)
        self.menu.addAction(self.action_user_login)
        self.menu.addAction(self.action_user_logout)
        self.menubar.addAction(self.menu_repo.menuAction())
        self.menubar.addAction(self.menu.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.menu_repo.setTitle(QtGui.QApplication.translate("MainWindow", "Хранилище", None, QtGui.QApplication.UnicodeUTF8))
        self.menu.setTitle(QtGui.QApplication.translate("MainWindow", "Пользователь", None, QtGui.QApplication.UnicodeUTF8))
        self.action_repo_create.setText(QtGui.QApplication.translate("MainWindow", "Создать", None, QtGui.QApplication.UnicodeUTF8))
        self.action_repo_open.setText(QtGui.QApplication.translate("MainWindow", "Открыть", None, QtGui.QApplication.UnicodeUTF8))
        self.action_repo_close.setText(QtGui.QApplication.translate("MainWindow", "Закрыть", None, QtGui.QApplication.UnicodeUTF8))
        self.action_repo_add_item.setText(QtGui.QApplication.translate("MainWindow", "Добавить элемент", None, QtGui.QApplication.UnicodeUTF8))
        self.action_user_create.setText(QtGui.QApplication.translate("MainWindow", "Создать", None, QtGui.QApplication.UnicodeUTF8))
        self.action_user_login.setText(QtGui.QApplication.translate("MainWindow", "Войти в хранилище", None, QtGui.QApplication.UnicodeUTF8))
        self.action_user_logout.setText(QtGui.QApplication.translate("MainWindow", "Выйти из хранилища", None, QtGui.QApplication.UnicodeUTF8))

