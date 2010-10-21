# -*- coding: utf-8 -*-
'''
Created on 20.08.2010

@author: vlkv
'''

import os.path
import sys

import PyQt4
import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui
from PyQt4.QtCore import (Qt, SIGNAL, QCoreApplication, QTextCodec)
from PyQt4.QtGui import (QApplication, QMainWindow, QDialog, QLineEdit, QTextBrowser, 
						QVBoxLayout, QPushButton, QFileDialog, QErrorMessage, QMessageBox, QLabel)
import ui_mainwindow
from item_dialog import ItemDialog
from repo_mgr import RepoMgr, UnitOfWork
from helpers import tr, showExcInfo, DialogMode
from db_model import Base, User, Item, DataRef, Tag, Field, FieldVal
import consts
from pyjavaproperties import Properties
from user_config import UserConfig
from user_dialog import UserDialog
from exceptions import LoginError

class TagCloud(QtGui.QTextEdit):
	'''
	Виджет для отображения облака тегов.
	'''
	def __init__(self, parent=None):
		super(TagCloud, self).__init__(parent)
		self.setReadOnly(True)
	
	def event(self, e):
		result = QtGui.QTextEdit.event(self, e)
		return result
	
	def mouseMoveEvent(self, e):
		cursor = self.cursorForPosition(e.pos())
		cursor.select(QtGui.QTextCursor.WordUnderCursor)
		word = cursor.selectedText()
		self.word = word
		
	def mouseDoubleClickEvent(self, e):
		if self.word != "" and self.word is not None:
			print("click on tag " + self.word)
			#TODO Выполняем фильтрацию элементов хранилища
	

class MainWindow(QMainWindow):
	'''
	Главное окно приложения reggata.
	'''
	
	#Текущее активное открытое хранилище (объект RepoMgr)
	__active_repo = None
	
	#Текущий пользователь, который работает с программой
	__active_user = None
	
	'''Модель таблицы для отображения элементов хранилища.'''
	model = None
	
	def __init__(self, parent=None):
		super(MainWindow, self).__init__(parent)
		self.ui = ui_mainwindow.Ui_MainWindow()
		self.ui.setupUi(self)
		self.connect(self.ui.action_repo_create, SIGNAL("triggered()"), self.action_repo_create)
		self.connect(self.ui.action_repo_close, SIGNAL("triggered()"), self.action_repo_close)
		self.connect(self.ui.action_repo_open, SIGNAL("triggered()"), self.action_repo_open)
		self.connect(self.ui.action_repo_add_item, SIGNAL("triggered()"), self.action_repo_add_item)
		self.connect(self.ui.action_user_create, SIGNAL("triggered()"), self.action_user_create)
		self.connect(self.ui.action_user_login, SIGNAL("triggered()"), self.action_user_login)
		self.connect(self.ui.action_user_logout, SIGNAL("triggered()"), self.action_user_logout)
		self.connect(self.ui.pushButton_query_exec, QtCore.SIGNAL("clicked()"), self.query_exec)
		
		#Добавляем на статус бар поля для отображения текущего хранилища и пользователя
		self.ui.label_repo = QLabel()
		self.ui.label_user = QLabel()
		self.ui.statusbar.addPermanentWidget(QLabel(tr("Хранилище:")))
		self.ui.statusbar.addPermanentWidget(self.ui.label_repo)
		self.ui.statusbar.addPermanentWidget(QLabel(tr("Пользователь:")))
		self.ui.statusbar.addPermanentWidget(self.ui.label_user)
		
		#Открываем последнее хранилище, с которым работал пользователь
		try:
			tmp = UserConfig().get("recent_repo.base_path")
			if tmp:
				self.active_repo = RepoMgr(tmp)
				
				#Пробуем залогиниться
				self._login_recent_user()
		except:
			pass
		
		self.ui.tag_cloud = TagCloud(self)
		self.ui.frame_tag_cloud.setLayout(QtGui.QVBoxLayout())
		self.ui.frame_tag_cloud.layout().addWidget(self.ui.tag_cloud)
		self.ui.tag_cloud.setText("<font size='+5'>Tag1</font>  asdf asdfa       adsf asdf <font size='+5'>Tag1</font> <font size='+1'>Tag1</font> <font size='+2'>Tag1</font> <font size='-2'>Tag1</font>")
		self.ui.tag_cloud.setMouseTracking(True)
				
		
		
	def query_exec(self):
		tags = self.ui.lineEdit_query.text().split()
		self.model.query(tags)
		
	
	def _login_recent_user(self):
		#Пробуем выполнить вход под логином/паролем последнего юзера
		try:
			login = UserConfig().get("recent_user.login")
			password = UserConfig().get("recent_user.password")
			uow = self.active_repo.createUnitOfWork()
			self.active_user = uow.loginUser(login, password)		
		finally:
			uow.close()
		
			
	def _set_active_user(self, user):
		if type(user) != User and user is not None:
			raise TypeError(tr("Параметр user должен иметь тип User."))
		self.__active_user = user
		
		if user is not None:
			self.ui.label_user.setText(user.login)
			
			#Запоминаем пользователя
			UserConfig().storeAll({"recent_user.login":user.login, "recent_user.password":user.password})
		else:
			self.ui.label_user.setText("")
		
		
	def _get_active_user(self):
		return self.__active_user
	
	active_user = property(_get_active_user, _set_active_user, doc="Текущий пользователь, который выполнил вход в хранилище.")
	
	
	def _set_active_repo(self, repo):
		if not isinstance(repo, RepoMgr) and not repo is None:
			raise TypeError(tr("Тип repo должен быть RepoMgr"))
	
		self.__active_repo = repo
			
		if repo is not None:
			#Запоминаем путь к хранилищу
			UserConfig().store("recent_repo.base_path", repo.base_path)
				
			#Если путь оканчивается на os.sep то os.path.split() возвращает ""
			(head, tail) = os.path.split(repo.base_path)
			while tail == "" and head != "":
				(head, tail) = os.path.split(head)
			self.ui.label_repo.setText(tail)
			
			#Выводим сообщение
			self.ui.statusbar.showMessage(tr("Открыто хранилище по адресу ") + repo.base_path, 3000)
			
			#Строим новую модель для таблицы
			self.model = RepoItemTableModel(repo)
			self.ui.tableView_items.setModel(self.model)
		else:
			self.ui.label_repo.setText("")
			self.model = None
			self.ui.tableView_items.setModel()
				
	def _get_active_repo(self):
		return self.__active_repo
	
	active_repo = property(_get_active_repo, _set_active_repo, doc="Текущее открытое хранилище.")
		
		
	def action_repo_create(self):
		try:
			base_path = QFileDialog.getExistingDirectory(self, tr("Выбор базовой директории хранилища"))
			if base_path == "":
				raise Exception(tr("Необходимо выбрать существующую директорию"))
			self.active_repo = RepoMgr.create_new_repo(base_path)
			self.active_user = None
		except Exception as ex:
			showExcInfo(self, ex)
			
		
	def action_repo_close(self):
		try:
			if self.active_repo is None:
				raise Exception(tr("Нет открытых хранилищ"))
			self.active_repo = None #Сборщик мусора и деструктор сделают свое дело
			self.active_user = None
		except Exception as ex:
			showExcInfo(self, ex)

	def action_repo_open(self):
		try:
			base_path = QFileDialog.getExistingDirectory(self, tr("Выбор базовой директории хранилища"))
			if base_path == "":
				raise Exception(tr("Необходимо выбрать базовую директорию существующего хранилища"))
			self.active_repo = RepoMgr(base_path)			
			self.active_user = None
			self._login_recent_user()
		
		except LoginError:
			#Отображаем диалог ввода логина/пароля (с возможностью отмены или создания нового юзера)
			ud = UserDialog(User(), self, mode=DialogMode.LOGIN)
			if ud.exec_():
				uow = self.active_repo.createUnitOfWork()
				try:				
					user = uow.loginUser(ud.user.login, ud.user.password)
					self.active_user = user
				except Exception as ex:
					showExcInfo(self, ex)
				finally:
					uow.close()
							
		except Exception as ex:
			showExcInfo(self, ex)
			
	def action_repo_add_item(self):
		try:
			if self.active_repo is None:
				raise Exception(tr("Необходимо сначала открыть хранилище."))
			
			if self.active_user is None:
				raise Exception(tr("Необходимо выполнить вход в хранилище."))
						
			it = Item(user_login=self.active_user.login)
			d = ItemDialog(it, self)
			if d.exec_():
				uow = self.active_repo.createUnitOfWork()
				try:
					uow.saveNewItem(d.item)
				finally:
					uow.close()
				#TODO refresh
				
		except Exception as ex:
			showExcInfo(self, ex)
	
	def action_user_create(self):
		try:
			if self.active_repo is None:
				raise Exception(tr("Необходимо сначала открыть хранилище."))
			
			u = UserDialog(User(), self)
			if u.exec_():
				uow = self.active_repo.createUnitOfWork()
				try:
					uow.saveNewUser(u.user)
					
					#Выполняем "вход" под новым юзером
					self.active_user = u.user					
				finally:
					uow.close()
		except Exception as ex:
			showExcInfo(self, ex)
		

	def action_user_login(self):
		try:
			ud = UserDialog(User(), self, mode=DialogMode.LOGIN)
			if ud.exec_():					
				uow = self.active_repo.createUnitOfWork()
				try:				
					user = uow.loginUser(ud.user.login, ud.user.password)
					self.active_user = user
				finally:
					uow.close()
		except Exception as ex:
			showExcInfo(self, ex)
	
	def action_user_logout(self):
		try:
			self.active_user = None
		except Exception as ex:
			showExcInfo(self, ex)
	
	def action_template(self):
		try:
			pass
		except Exception as ex:
			showExcInfo(self, ex)


class RepoItemTableModel(QtCore.QAbstractTableModel):
	
	ID = 0
	TITLE = 1
	
	def __init__(self, repo):
		super(RepoItemTableModel, self).__init__()
		self.repo = repo
		self.items = []
		
	def query(self, and_tags=[]):
		uow = self.repo.createUnitOfWork()
		try:
			self.items = uow.queryItems(and_tags)
#			print(self.items)
			self.reset()
		finally:
			uow.close()
	
	def rowCount(self, index=QtCore.QModelIndex()):
		return len(self.items)
	
	def columnCount(self, index=QtCore.QModelIndex()):
		return 2
	
	def data(self, index, role=Qt.DisplayRole):
		if not index.isValid() or \
			not (0 <= index.row() < len(self.items)):
			return None
		
		item = self.items[index.row()]
		column = index.column()
		if role == Qt.DisplayRole:
			if column == self.ID:
				return item.id
			elif column == self.TITLE:
				return item.title
			
		elif role == Qt.TextAlignmentRole:
			if column == self.ID:
				return int(Qt.AlignRight | Qt.AlignVCenter)
			else:
				return int(Qt.AlignLeft | Qt.AlignVCenter)
			
		else:
			return None
		
		


if __name__ == '__main__':
	

	app = QApplication(sys.argv)
	form = MainWindow()
	form.show()
	app.exec_()

#	path = '../test.sqlite'
#	if os.path.isfile(path):
#		conn = sqlite3.connect(path)
#		try:
#			c = conn.cursor()
#			c.execute('''insert into "data"
#				  (uri, size) values ('path_to_file 4', '10243434')''')
#			conn.commit()
#			c.close()
#		except:
#			print 'error: ', sys.exc_info()
#		finally:
#			conn.close()
#
#	else:
#		print 'file not found ', path
