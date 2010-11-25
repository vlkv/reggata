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

Created on 20.08.2010

@author: vlkv
'''
import os.path
import sys
import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui
import ui_mainwindow
from item_dialog import ItemDialog
from repo_mgr import RepoMgr, UnitOfWork
from helpers import tr, showExcInfo, DialogMode, scale_value, is_none_or_empty
from db_model import Base, User, Item, DataRef, Tag, Field, Item_Field
from user_config import UserConfig
from user_dialog import UserDialog
from exceptions import LoginError, MsgException
import query_parser
from tag_cloud import TagCloud

#TODO Исправить виджеты на ItemDialog-е, вызванные переходом на новую схему БД
#TODO Добавить поиск и отображение объектов DataRef, не привязанных ни к одному Item-у
#TODO Добавить поиск Item-ов, DataRef которых ссылается на несуществующий файл
#TODO Вычислять хеши от содержимого файлов и отображать диалог ожидания во время добавления файла
#TODO Сделать нормальный разбор Ключ=Значение в ItemDialog (А то если поставить пробел до или после =, то не работает)
#TODO Сделать отображение Item-ов, у которых нет ни одного тега
#TODO Реализовать до конца грамматику языка запросов (прежде всего фильтрацию по директориям и пользователям)
#TODO Сделать настраиваемый механизм вызова соответствующей программы при двойном клике по Item-у
#TODO Сделать функции экспорта результатов поиска во внешнюю директорию
#TODO Сделать проект механизма клонирования/синхронизации хранилищ
#TODO Сделать возможность привязывать несколько файлов к одному Item-у при помощи архивирования их на лету (при помощи zip, например)
#TODO Сделать новый тип объекта DataRef для сохранения ссылок на директории. Тогда можно будет привязывать теги и поля к директориям внутри хранилища. Надо еще подумать, стоит ли такое реализовывать или нет.

class MainWindow(QtGui.QMainWindow):
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
		self.connect(self.ui.action_repo_create, QtCore.SIGNAL("triggered()"), self.action_repo_create)
		self.connect(self.ui.action_repo_close, QtCore.SIGNAL("triggered()"), self.action_repo_close)
		self.connect(self.ui.action_repo_open, QtCore.SIGNAL("triggered()"), self.action_repo_open)
		self.connect(self.ui.action_item_add, QtCore.SIGNAL("triggered()"), self.action_item_add)
		self.connect(self.ui.action_item_edit, QtCore.SIGNAL("triggered()"), self.action_item_edit)
		self.connect(self.ui.action_user_create, QtCore.SIGNAL("triggered()"), self.action_user_create)
		self.connect(self.ui.action_user_login, QtCore.SIGNAL("triggered()"), self.action_user_login)
		self.connect(self.ui.action_user_logout, QtCore.SIGNAL("triggered()"), self.action_user_logout)
		self.connect(self.ui.pushButton_query_exec, QtCore.SIGNAL("clicked()"), self.query_exec)
		self.connect(self.ui.lineEdit_query, QtCore.SIGNAL("returnPressed()"), self.ui.pushButton_query_exec.click)
		self.connect(self.ui.pushButton_query_reset, QtCore.SIGNAL("clicked()"), self.query_reset)
		
		
		#Добавляем на статус бар поля для отображения текущего хранилища и пользователя
		self.ui.label_repo = QtGui.QLabel()
		self.ui.label_user = QtGui.QLabel()
		self.ui.statusbar.addPermanentWidget(QtGui.QLabel(self.tr("Repository:")))
		self.ui.statusbar.addPermanentWidget(self.ui.label_repo)
		self.ui.statusbar.addPermanentWidget(QtGui.QLabel(self.tr("User:")))
		self.ui.statusbar.addPermanentWidget(self.ui.label_user)
		
		#Добавляем облако тегов
		self.ui.tag_cloud = TagCloud(self)
		self.ui.dockWidget_tag_cloud.setWidget(self.ui.tag_cloud)
		self.connect(self.ui.tag_cloud, QtCore.SIGNAL("selectedTagsChanged"), self.selected_tags_changed)
		
		self.connect(self.ui.lineEdit_query, QtCore.SIGNAL("textEdited(QString)"), self.reset_tag_cloud)
		
		#Открываем последнее хранилище, с которым работал пользователь
		try:
			tmp = UserConfig().get("recent_repo.base_path")
			if tmp:
				self.active_repo = RepoMgr(tmp)
				
				#Пробуем залогиниться
				self._login_recent_user()
		except:
			pass
		
		#В третьей колонке отображаем миниатюры изображений
		self.ui.tableView_items.setItemDelegateForColumn(2, ImageThumbDelegate())

	def reset_tag_cloud(self):
		self.ui.tag_cloud.reset()
	
	def selected_tags_changed(self):
		#TODO Нужно заключать в кавычки имена тегов, содержащие недопустимые символы
		text = ""
		for tag in self.ui.tag_cloud.tags:
			text = text + tag + " "
		for tag in self.ui.tag_cloud.not_tags:
			text = text + query_parser.NOT_OPERATOR + " " + tag + " "
		text = self.ui.lineEdit_query.setText(text)
		self.query_exec()
		
		
		
		
			
		
	def query_reset(self):
		self.ui.lineEdit_query.setText("")
		if self.model:
			self.model.query("")
		self.ui.tag_cloud.reset()
		
		
	def query_exec(self):
		query_text = self.ui.lineEdit_query.text()
		self.model.query(query_text)
		
	
	def _login_recent_user(self):
		#Пробуем выполнить вход под логином/паролем последнего юзера
		try:
			login = UserConfig().get("recent_user.login")
			password = UserConfig().get("recent_user.password")
			uow = self.active_repo.createUnitOfWork()
			self.active_user = uow.login_user(login, password)
		finally:
			uow.close()
		
			
	def _set_active_user(self, user):
		if type(user) != User and user is not None:
			raise TypeError(self.tr("Argument must be an instance of User class."))
		
		#Убираем из облака старый логин
		if self.__active_user is not None:
			self.ui.tag_cloud.remove_user(self.__active_user.login)			
		
		self.__active_user = user
		
		#Добавляем в облако новый логин
		if user is not None:
			self.ui.tag_cloud.add_user(user.login)
		
		
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
			raise TypeError(self.tr("Argument must be of RepoMgr class."))
	
		self.__active_repo = repo
		
		#Передаем новое хранилище виджету "облако тегов"
		self.ui.tag_cloud.repo = repo
		
		if repo is not None:
			#Запоминаем путь к хранилищу
			UserConfig().store("recent_repo.base_path", repo.base_path)
				
			#Если путь оканчивается на os.sep то os.path.split() возвращает ""
			(head, tail) = os.path.split(repo.base_path)
			while tail == "" and head != "":
				(head, tail) = os.path.split(head)
			self.ui.label_repo.setText(tail)
			
			#Выводим сообщение
			self.ui.statusbar.showMessage(self.tr("Opened repository from {}.").format(repo.base_path), 5000)
			
			#Строим новую модель для таблицы
			self.model = RepoItemTableModel(repo)
			self.ui.tableView_items.setModel(self.model)
		else:
			self.ui.label_repo.setText("")
			self.model = None
			self.ui.tableView_items.setModel(None)
				
	def _get_active_repo(self):
		return self.__active_repo
	
	active_repo = property(_get_active_repo, _set_active_repo, doc="Текущее открытое хранилище.")
		
		
	def action_repo_create(self):
		try:
			base_path = QtGui.QFileDialog.getExistingDirectory(self, self.tr("Choose a base path for new repository"))
			if base_path == "":
				raise Exception(self.tr("You haven't chosen existent directory. Operation canceled."))
			self.active_repo = RepoMgr.create_new_repo(base_path)
			self.active_user = None
		except Exception as ex:
			showExcInfo(self, ex)
			
		
	def action_repo_close(self):
		try:
			if self.active_repo is None:
				raise Exception(self.tr("There is no opened repository."))
			self.active_repo = None #Сборщик мусора и деструктор сделают свое дело
			self.active_user = None
		except Exception as ex:
			showExcInfo(self, ex)

	def action_repo_open(self):
		try:
			base_path = QtGui.QFileDialog.getExistingDirectory(self, self.tr("Choose a repository base path"))
			if base_path == "":
				raise Exception(self.tr("You haven't chosen existent directory. Operation canceled."))
			self.active_repo = RepoMgr(base_path)			
			self.active_user = None
			self._login_recent_user()
		
		except LoginError:
			#Отображаем диалог ввода логина/пароля (с возможностью отмены или создания нового юзера)
			ud = UserDialog(User(), self, mode=DialogMode.LOGIN)
			if ud.exec_():
				uow = self.active_repo.createUnitOfWork()
				try:				
					user = uow.login_user(ud.user.login, ud.user.password)
					self.active_user = user
				except Exception as ex:
					showExcInfo(self, ex)
				finally:
					uow.close()
							
		except Exception as ex:
			showExcInfo(self, ex)
			
	def action_item_add(self):
		try:
			if self.active_repo is None:
				raise MsgException(self.tr("Open a repository first."))
			
			if self.active_user is None:
				raise MsgException(self.tr("Login to a repository first."))
			
			#Просим пользователя выбрать один или более файлов
			file = QtGui.QFileDialog.getOpenFileName(self, self.tr("Select file to add"))
			if is_none_or_empty(file):
				return
			
			#Сразу привязываем выбранный файл к новому элементу
			item = Item(user_login=self.active_user.login)
			item.title = os.path.basename(file) #Предлагаем назвать элемент по имени файла			
			item.data_ref = DataRef(url=file, type="FILE")
						
			#Открываем диалог для ввода остальной информации об элементе
			d = ItemDialog(item, self, DialogMode.CREATE)
			if d.exec_():
				uow = self.active_repo.createUnitOfWork()
				try:
					uow.save_new_item(d.item, self.active_user.login)
				finally:
					uow.close()
				#TODO refresh
				
		except Exception as ex:
			showExcInfo(self, ex)
	
	def action_user_create(self):
		try:
			if self.active_repo is None:
				raise Exception(self.tr("Open a repository first."))
			
			u = UserDialog(User(), self)
			if u.exec_():
				uow = self.active_repo.createUnitOfWork()
				try:
					uow.save_new_user(u.user)
					
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
					user = uow.login_user(ud.user.login, ud.user.password)
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


	def action_item_edit(self):
		try:
			if self.active_repo is None:
				raise MsgException(self.tr("Open a repository first."))
			
			if self.active_user is None:
				raise MsgException(self.tr("Login to a repository first."))
			
			#Нужно множество, т.к. в результате selectedIndexes() могут быть дубликаты
			rows = set()
			for idx in self.ui.tableView_items.selectionModel().selectedIndexes():
				rows.add(idx.row())
			
			if len(rows) == 0:
				raise MsgException(self.tr("There are no selected items."))
			
			if len(rows) > 1:
				raise MsgException(self.tr("Please select only one item."))
						
			item_id = self.model.items[rows.pop()].id
			uow = self.active_repo.createUnitOfWork()
			try:
				item = uow.get_item(item_id)
				item_dialog = ItemDialog(item, self, DialogMode.EDIT)
				if item_dialog.exec_():
					uow.update_existing_item(item_dialog.item, self.active_user.login)
															
			finally:
				uow.close()
			
		except Exception as ex:
			showExcInfo(self, ex)
	
	def action_template(self):
		try:
			pass
		except Exception as ex:
			showExcInfo(self, ex)
			



class ImageThumbDelegate(QtGui.QAbstractItemDelegate):
	'''Делегат, для отображения миниатюры файла-изображения в таблице элементов
	хранилища.'''
	def sizeHint(self, option, index):
		return QtCore.QSize(option.rect)
   
	def paint(self, painter, option, index):
		
		
		model = index.model()
		item = model.items[index.row()]
		print("title = " + item.title)
		
		image = QtGui.QImage(index.data())
		if image:
		    painter.drawImage(option.rect, image)
    
	    #TODO Нужно кешировать сгенерированные миниматюры
	    #Потому что так как сейчас --- очень неэффективно и медленно! 
    	


class RepoItemTableModel(QtCore.QAbstractTableModel):
	'''Модель таблицы, отображающей элементы хранилища.'''
	
	ID = 0
	TITLE = 1
	IMAGE_THUMB = 2
	
	def __init__(self, repo):
		super(RepoItemTableModel, self).__init__()
		self.repo = repo
		self.items = []
		
	def query(self, query_text):
		'''Выполняет извлечение элементов из хранилища.'''
		
		if query_text is None or query_text.strip()=="":
			self.items = []
			self.reset()
			return
		
		uow = self.repo.createUnitOfWork()
		try:
			tree = query_parser.parser.parse(query_text)
			sql = tree.interpret()
			self.items = uow.query_items_by_sql(sql)

			self.reset()
		finally:
			uow.close()
	
	def rowCount(self, index=QtCore.QModelIndex()):
		return len(self.items)
	
	def columnCount(self, index=QtCore.QModelIndex()):
		return 3
	
	def data(self, index, role=QtCore.Qt.DisplayRole):
		if not index.isValid() or not (0 <= index.row() < len(self.items)):
			return None
		
		item = self.items[index.row()]
		column = index.column()
		
		if role == QtCore.Qt.DisplayRole:
			if column == self.ID:
				return item.id
			elif column == self.TITLE:
				return item.title
#			elif column == self.IMAGE_THUMB:
#				return self.repo.base_path + os.sep + item.data_ref.url if item.data_ref else None
			else:
				return None
			
		elif role == QtCore.Qt.TextAlignmentRole:
			if column == self.ID:
				return int(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
			elif column == self.TITLE:
				return int(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
			else:
				return None
			
		else:
			return None
		
		


if __name__ == '__main__':
	
	app = QtGui.QApplication(sys.argv)
	
	qtr = QtCore.QTranslator()
	if qtr.load("reggata_ru.qm", ".."):
		app.installTranslator(qtr)
	else:
		print("Cannot find translation files.")
	
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
