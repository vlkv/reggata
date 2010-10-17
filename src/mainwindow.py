# -*- coding: utf-8 -*-
'''
Created on 20.08.2010

@author: vlkv
'''

import sqlite3
import os.path
import sys

import PyQt4
import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui
from PyQt4.QtCore import (Qt, SIGNAL, QCoreApplication, QTextCodec)
from PyQt4.QtGui import (QApplication, QMainWindow, QDialog, QLineEdit, QTextBrowser, 
						QVBoxLayout, QPushButton, QFileDialog, QErrorMessage, QMessageBox, QLabel)
import ui_mainwindow
from itemdialog import ItemDialog
from repo_mgr import RepoMgr, UnitOfWork
from helpers import tr, showExcInfo

import sqlalchemy as sqa
from sqlalchemy.ext.declarative import declarative_base
from db_model import Base, User, Item, DataRef, Tag, Field, FieldVal 
import consts

from pyjavaproperties import Properties
from _pyio import open
from user_config import UserConfig



class MainWindow(QMainWindow):
	'''
	Главное окно приложения reggata.
	'''
	
	#Текущее активное открытое хранилище (объект RepoMgr)
	__active_repo = None
	
	#Текущий пользователь, который работает с программой
	__user = None
	
	def __init__(self, parent=None):
		super(MainWindow, self).__init__(parent)
		self.ui = ui_mainwindow.Ui_MainWindow()
		self.ui.setupUi(self)
		self.connect(self.ui.action_repo_create, SIGNAL("triggered()"), self.action_repo_create)
		self.connect(self.ui.action_repo_close, SIGNAL("triggered()"), self.action_repo_close)
		self.connect(self.ui.action_repo_open, SIGNAL("triggered()"), self.action_repo_open)
		self.connect(self.ui.action_repo_add_item, SIGNAL("triggered()"), self.action_repo_add_item)
		
		#Добавляем на статус бар поля для отображения текущего хранилища и пользователя
		self.ui.label_repo = QLabel()
		self.ui.label_user = QLabel()
		self.ui.statusbar.addPermanentWidget(QLabel(tr("Хранилище:")))
		self.ui.statusbar.addPermanentWidget(self.ui.label_repo)
		self.ui.statusbar.addPermanentWidget(QLabel(tr("Пользователь:")))
		self.ui.statusbar.addPermanentWidget(self.ui.label_user)
		
		#Открываем последнее хранилище, с которым работал пользователь 
		tmp = UserConfig().get("recent_repo.base_path")
		if tmp:
			self.active_repo = RepoMgr(tmp)
			
			
			
	
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
		else:
			self.ui.label_repo.setText("")
			
	
	
	def _get_active_repo(self):
		return self.__active_repo
	
	active_repo = property(_get_active_repo, _set_active_repo, "Текущее открытое хранилище.")
		
		
	def action_repo_create(self):
		try:
			base_path = QFileDialog.getExistingDirectory(self, tr("Выбор базовой директории хранилища"))
			if base_path == "":
				raise Exception(tr("Необходимо выбрать существующую директорию"))
			self.active_repo = RepoMgr.create_new_repo(base_path)			
		except Exception as ex:
			QMessageBox.information(self, tr("Отмена операции"), str(ex))
			
		
	def action_repo_close(self):
		try:
			if self.active_repo is None:
				raise Exception(tr("Нет открытых хранилищ"))
			self.active_repo = None #Сборщик мусора и деструктор сделают свое дело
		except Exception as ex:
			showExcInfo(self, ex)

	def action_repo_open(self):
		try:
			base_path = QFileDialog.getExistingDirectory(self, tr("Выбор базовой директории хранилища"))
			if base_path == "":
				raise Exception(tr("Необходимо выбрать базовую директорию существующего хранилища"))
			self.active_repo = RepoMgr(base_path)
			
		except Exception as ex:
			QMessageBox.information(self, tr("Ошибка"), str(ex))
			
	def action_repo_add_item(self):
		try:
			if self.active_repo is None:
				raise Exception(tr("Необходимо сначала открыть хранилище."))
			
			
			d = ItemDialog(Item(), self)
			if d.exec_():
				uow = self.active_repo.createUnitOfWork()
				try:
					uow.saveNewItem(d.item)
				finally:
					uow.close()
				#TODO refresh
				
	
		except Exception as ex:		
			QMessageBox.information(self, tr("Ошибка"), str(ex))
			
	def action_template(self):
		try:			
			pass
		except Exception as ex:
			QMessageBox.information(self, tr("Ошибка"), str(ex))

#class MainWindow(QDialog):
#
#	def __init__(self, parent=None):
#		super(MainWindow, self).__init__(parent)
#		self.setWindowTitle("datorg - главное окно")
#		self.browser = QTextBrowser()
#		self.lineedit = QLineEdit("Type an expression and press Enter")
#		self.lineedit.selectAll()
#
#		layout = QVBoxLayout()
#		layout.addWidget(self.browser)
#		layout.addWidget(self.lineedit)
#		self.setLayout(layout)
#
#		self.lineedit.setFocus()
#		self.connect(self.lineedit, SIGNAL("returnPressed()"), self.updateUi)
#
#
#		self.button = QPushButton("Eval")
#		layout.addWidget(self.button)
#		self.connect(self.button, SIGNAL("pressed()"), self.updateUi)
#
#
#	def updateUi(self):
#		try:
#			text = self.lineedit.text()
#			self.browser.append("{0} = <b>{1}</b>".format(text, eval(text)))
#		except:
#			self.browser.append("<font color=red>{0} is invalid!</font>".format(text))



if __name__ == '__main__':
	
#	engine = sqa.create_engine("sqlite:///" + consts.DB_FILE)
#	Base.metadata.create_all(engine)

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
