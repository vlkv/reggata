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
from PyQt4.QtCore import Qt
import ui_mainwindow
from item_dialog import ItemDialog
from repo_mgr import RepoMgr, UnitOfWork, BackgrThread, UpdateGroupOfItemsThread,\
	CreateGroupIfItemsThread
from helpers import tr, show_exc_info, DialogMode, scale_value, is_none_or_empty,\
	WaitDialog, raise_exc
from db_schema import Base, User, Item, DataRef, Tag, Field, Item_Field
from user_config import UserConfig
from user_dialog import UserDialog
from exceptions import LoginError, MsgException
from parsers import query_parser
from tag_cloud import TagCloud
import consts
from items_dialog import ItemsDialog
from ext_app_mgr import ExtAppMgr


#TODO Добавить поиск и отображение объектов DataRef, не привязанных ни к одному Item-у
#TODO Добавить поиск Item-ов, DataRef которых ссылается на несуществующий файл
#TODO Сделать нормальный разбор Ключ=Значение в ItemDialog (А то если поставить пробел до или после =, то не работает)
#TODO Сделать отображение Item-ов, у которых нет ни одного тега
#TODO Реализовать до конца грамматику языка запросов (прежде всего фильтрацию по директориям и пользователям)
#TODO Сделать функции экспорта результатов поиска во внешнюю директорию
#TODO Сделать проект механизма клонирования/синхронизации хранилищ
#TODO Сделать возможность привязывать несколько файлов к одному Item-у при помощи архивирования их на лету (при помощи zip, например)
#TODO Сделать новый тип объекта DataRef для сохранения ссылок на директории. Тогда можно будет привязывать теги и поля к директориям внутри хранилища. Надо еще подумать, стоит ли такое реализовывать или нет.
#TODO Сделать встроенный просмотрщик графических файлов.

class MainWindow(QtGui.QMainWindow):
	'''
	Главное окно приложения reggata.
	'''
	
	def __init__(self, parent=None):
		super(MainWindow, self).__init__(parent)
		self.ui = ui_mainwindow.Ui_MainWindow()
		self.ui.setupUi(self)
		
		#Текущее активное открытое хранилище (объект RepoMgr)
		self.__active_repo = None
		
		#Текущий пользователь, который работает с программой
		self.__active_user = None
		
		#Модель таблицы для отображения элементов хранилища
		self.model = None	
		
		self.connect(self.ui.action_repo_create, QtCore.SIGNAL("triggered()"), self.action_repo_create)
		self.connect(self.ui.action_repo_close, QtCore.SIGNAL("triggered()"), self.action_repo_close)
		self.connect(self.ui.action_repo_open, QtCore.SIGNAL("triggered()"), self.action_repo_open)
		
		self.connect(self.ui.action_user_create, QtCore.SIGNAL("triggered()"), self.action_user_create)
		self.connect(self.ui.action_user_login, QtCore.SIGNAL("triggered()"), self.action_user_login)
		self.connect(self.ui.action_user_logout, QtCore.SIGNAL("triggered()"), self.action_user_logout)
		self.connect(self.ui.action_user_change_pass, QtCore.SIGNAL("triggered()"), self.action_user_change_pass)
		
		self.connect(self.ui.action_item_add, QtCore.SIGNAL("triggered()"), self.action_item_add)
		self.connect(self.ui.action_item_edit, QtCore.SIGNAL("triggered()"), self.action_item_edit)
		self.connect(self.ui.action_item_add_many, QtCore.SIGNAL("triggered()"), self.action_item_add_many)
		self.connect(self.ui.action_item_view, QtCore.SIGNAL("triggered()"), self.action_item_view)
		self.connect(self.ui.tableView_items, QtCore.SIGNAL("doubleClicked(QModelIndex)"), self.action_item_view) 
		
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
		self.connect(self.ui.action_tools_tag_cloud, QtCore.SIGNAL("triggered(bool)"), lambda b: self.ui.dockWidget_tag_cloud.setVisible(b))
		self.connect(self.ui.dockWidget_tag_cloud, QtCore.SIGNAL("visibilityChanged(bool)"), lambda b: self.ui.action_tools_tag_cloud.setChecked(b))
		
		self.connect(self.ui.lineEdit_query, QtCore.SIGNAL("textEdited(QString)"), self.reset_tag_cloud)
		
		#Открываем последнее хранилище, с которым работал пользователь
		try:
			tmp = UserConfig()["recent_repo.base_path"]
			self.active_repo = RepoMgr(tmp)
			self._login_recent_user()
		except:
			self.ui.statusbar.showMessage(self.tr("Cannot open/login recent repository."), 5000)
		
		#В третьей колонке отображаем миниатюры изображений
		self.ui.tableView_items.setItemDelegateForColumn(RepoItemTableModel.IMAGE_THUMB, ImageThumbDelegate()) 		
		#Работает в PyQt начиная с 4.8.1. В PyQt 4.7.3 не работает!
		
		#Для старых версий PyQt задаем его для всей таблицы:
#		self.ui.tableView_items.setItemDelegate(ImageThumbDelegate()) 
		
		#Пытаемся восстанавливить размер окна, как был при последнем запуске
		try:
			width = int(UserConfig().get("main_window.width", 640))
			height = int(UserConfig().get("main_window.height", 480))
			self.resize(width, height)
		except:
			pass
		
		#Делаем так, чтобы размер окна сохранялся при изменении
		self.save_state_timer = QtCore.QTimer(self)
		self.save_state_timer.setSingleShot(True)
		self.connect(self.save_state_timer, QtCore.SIGNAL("timeout()"), self.save_main_window_state)
		
		#Восстанавливаем размер облака тегов
		self.ui.tag_cloud.hint_height = int(UserConfig().get("main_window.tag_cloud.height", 100))
		self.ui.tag_cloud.hint_width = int(UserConfig().get("main_window.tag_cloud.width", 100))
		self.connect(self.ui.tag_cloud, QtCore.SIGNAL("maySaveSize"), self.save_main_window_state)
		dock_area = int(UserConfig().get("main_window.tag_cloud.dock_area", QtCore.Qt.TopDockWidgetArea))
		self.removeDockWidget(self.ui.dockWidget_tag_cloud)
		self.addDockWidget(dock_area if dock_area != Qt.NoDockWidgetArea else QtCore.Qt.TopDockWidgetArea, self.ui.dockWidget_tag_cloud)
		self.ui.dockWidget_tag_cloud.show()


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
	
	def save_main_window_state(self):
		#Тут нужно сохранить в конфиге пользователя размер окна
		UserConfig().storeAll({"main_window.width":self.width(), "main_window.height":self.height()})
		
		#Размер облака тегов
		UserConfig().storeAll({"main_window.tag_cloud.width":self.ui.tag_cloud.hint_width, "main_window.tag_cloud.height":self.ui.tag_cloud.hint_height})
		
		#Расположение облака тегов
		UserConfig().store("main_window.tag_cloud.dock_area", str(self.dockWidgetArea(self.ui.dockWidget_tag_cloud)))
		
		self.ui.statusbar.showMessage(self.tr("Main window state has saved."), 5000)
		
	def resizeEvent(self, resize_event):
		self.save_state_timer.start(3000) #Повторный вызов start() делает перезапуск таймера 
			
		
	def query_reset(self):
		self.ui.lineEdit_query.setText("")
		if self.model:
			self.model.query("")
		self.ui.tag_cloud.reset()
		
		
	def query_exec(self):
		try:
			if not self.active_repo:
				raise MsgException(self.tr("Open a repository first."))
			query_text = self.ui.lineEdit_query.text()
			self.model.query(query_text)
			self.ui.tableView_items.resizeColumnsToContents()
			self.ui.tableView_items.resizeRowsToContents()
		except Exception as ex:
			show_exc_info(self, ex)
		
		
	
	def _login_recent_user(self):
		'''Функция пробует выполнить вход в текущее хранилище под логином/паролем последнего юзера.
		Если что не так, данная функция выкидывает исключение.'''
		
		if self.active_repo is None:
			raise MsgException(self.tr("You cannot login because there is no opened repo."))
		
		login = UserConfig().get("recent_user.login")
		password = UserConfig().get("recent_user.password")
		#login и password могут оказаться равны None (если не найдены). 
		#Это значит, что uow.login_user() выкинет LoginError
		
		uow = self.active_repo.create_unit_of_work()
		try:
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
			self.ui.label_user.setText("<b>" + user.login + "</b>")
			
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
				
			#Отображаем в статус-баре имя хранилища
			#Если путь оканчивается на os.sep то os.path.split() возвращает ""
			(head, tail) = os.path.split(repo.base_path)
			while tail == "" and head != "":
				(head, tail) = os.path.split(head)
			self.ui.label_repo.setText("<b>" + tail + "</b>")
			
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
			if not base_path:
				raise MsgException(self.tr("You haven't chosen existent directory. Operation canceled."))
			self.active_repo = RepoMgr.create_new_repo(base_path)
			self.active_user = None
		except Exception as ex:
			show_exc_info(self, ex)
			
		
	def action_repo_close(self):
		try:
			if self.active_repo is None:
				raise MsgException(self.tr("There is no opened repository."))
			self.active_repo = None #Сборщик мусора и деструктор сделают свое дело
			self.active_user = None
		except Exception as ex:
			show_exc_info(self, ex)

	def action_repo_open(self):
		try:
			base_path = QtGui.QFileDialog.getExistingDirectory(self, self.tr("Choose a repository base path"))
			if not base_path:
				raise Exception(self.tr("You haven't chosen existent directory. Operation canceled."))
			self.active_repo = RepoMgr(base_path)			
			self.active_user = None
			self._login_recent_user()
		
		except LoginError:
			#Отображаем диалог ввода логина/пароля (с возможностью отмены или создания нового юзера)
			ud = UserDialog(User(), self, mode=DialogMode.LOGIN)
			if ud.exec_():
				uow = self.active_repo.create_unit_of_work()
				try:				
					user = uow.login_user(ud.user.login, ud.user.password)
					self.active_user = user
				except Exception as ex:
					show_exc_info(self, ex)
				finally:
					uow.close()
							
		except Exception as ex:
			show_exc_info(self, ex)
	

			
	def action_item_view(self):
		try:
			sel_indexes = self.ui.tableView_items.selectionModel().selectedIndexes()
			if len(sel_indexes) > 1:
				raise MsgException(self.tr("Select only one item, please."))
			
			sel_row = sel_indexes[0].row()			
			data_ref = self.model.items[sel_row].data_ref
			
			if not data_ref or data_ref.type != DataRef.FILE:
				raise MsgException(self.tr("Action 'View item' can be applied only to items linked with files."))
			
			eam = ExtAppMgr()
			eam.invoke(os.path.join(self.active_repo.base_path, data_ref.url))
			
			
			
		except Exception as ex:
			show_exc_info(self, ex)
		else:
			self.ui.statusbar.showMessage(self.tr("Operation completed."), 5000)
		
	def action_item_add_many(self):
		'''Добавление нескольких элементов в хранилище. При этом ко всем добавляемым
		файлам привязываются одинаковые теги и поля. И они копируются в одну и ту 
		же директорию хранилища. Название title каждого элемента будет совпадать с
		именем добавляемого файла.'''
		try:
			if self.active_repo is None:
				raise MsgException(self.tr("Open a repository first."))
			
			if self.active_user is None:
				raise MsgException(self.tr("Login to a repository first."))
			
			#Просим пользователя выбрать файлы
#			file_dialog = QtGui.QFileDialog(self, self.tr("Select files and directories to add"))
#			file_dialog.setFileMode(QtGui.QFileDialog.Directory)
#			if file_dialog.exec_() == QtGui.QDialog.Accepted:
#				files = file_dialog.selectedFiles()
#				for file in files:
#					print(file)

			#TODO Надо сделать функцию рекурсивного добавления множества файлов из директории
				
					
			files = QtGui.QFileDialog.getOpenFileNames(self, self.tr("Select file to add"))
			if len(files) == 0:
				raise MsgException(self.tr("No files chosen. Operation cancelled."))
			
			items = []
			for file in files:
				item = Item(user_login=self.active_user.login)
				item.title = os.path.basename(file)
				item.data_ref = DataRef(url=file, type=DataRef.FILE)
				items.append(item)
			
			#Открываем диалог для ввода информации о тегах и полях
			d = ItemsDialog(self, items, DialogMode.CREATE)
			if d.exec_():
				
				thread = CreateGroupIfItemsThread(self, self.active_repo, items)
				self.connect(thread, QtCore.SIGNAL("exception"), lambda msg: raise_exc(msg))
										
				#TODO Тут надо отображать WaitDialog
				wd = WaitDialog(self)
				self.connect(thread, QtCore.SIGNAL("finished"), wd.reject)
				self.connect(thread, QtCore.SIGNAL("exception"), wd.exception)
				self.connect(thread, QtCore.SIGNAL("progress"), wd.set_progress)
									
				thread.start()
				thread.wait(1000)
				if thread.isRunning():
					wd.exec_()
				
		except Exception as ex:
			show_exc_info(self, ex)
		else:
			self.ui.statusbar.showMessage(self.tr("Operation completed."), 5000)
			#TODO refresh
		
		
	def action_item_add(self):
		'''Добавление одного элемента в хранилище.'''
		try:
			if self.active_repo is None:
				raise MsgException(self.tr("Open a repository first."))
			
			if self.active_user is None:
				raise MsgException(self.tr("Login to a repository first."))
			
			#Создаем новый (пустой пока) элемент
			item = Item(user_login=self.active_user.login)
			
			#Просим пользователя выбрать один файл
			file = QtGui.QFileDialog.getOpenFileName(self, self.tr("Select file to add"))
			if not is_none_or_empty(file):
				#Сразу привязываем выбранный файл к новому элементу
				item.title = os.path.basename(file) #Предлагаем назвать элемент по имени файла			
				item.data_ref = DataRef(url=file, type=DataRef.FILE)
			
						
			#Открываем диалог для ввода остальной информации об элементе
			d = ItemDialog(item, self, DialogMode.CREATE)
			if d.exec_():
				uow = self.active_repo.create_unit_of_work()
				try:
					#uow.save_new_item(d.item, self.active_user.login)
					thread = BackgrThread(self, uow.save_new_item, d.item, self.active_user.login)
					
					wd = WaitDialog(self, indeterminate=True)
					self.connect(thread, QtCore.SIGNAL("finished"), wd.reject)
					self.connect(thread, QtCore.SIGNAL("exception"), wd.exception)
										
					thread.start()
					thread.wait(1000)
					if thread.isRunning():
						wd.exec_()
										
				finally:
					uow.close()
				
				
		except Exception as ex:
			show_exc_info(self, ex)
		else:
			self.ui.statusbar.showMessage(self.tr("Operation completed."), 5000)
			#TODO refresh
	
	def action_user_create(self):
		try:
			if self.active_repo is None:
				raise Exception(self.tr("Open a repository first."))
			
			u = UserDialog(User(), self)
			if u.exec_():
				uow = self.active_repo.create_unit_of_work()
				try:
					uow.save_new_user(u.user)
					
					#Выполняем "вход" под новым юзером
					self.active_user = u.user					
				finally:
					uow.close()
		except Exception as ex:
			show_exc_info(self, ex)
		

	def action_user_change_pass(self):
		try:
			#TODO
			raise NotImplementedError("This function is not implemented yet.")
		except Exception as ex:
			show_exc_info(self, ex)
		else:
			self.ui.statusbar.showMessage(self.tr("Operation completed."), 5000)
		
		

	def action_user_login(self):
		try:
			ud = UserDialog(User(), self, mode=DialogMode.LOGIN)
			if ud.exec_():					
				uow = self.active_repo.create_unit_of_work()
				try:				
					user = uow.login_user(ud.user.login, ud.user.password)
					self.active_user = user
				finally:
					uow.close()
		except Exception as ex:
			show_exc_info(self, ex)
	
	def action_user_logout(self):
		try:
			self.active_user = None
		except Exception as ex:
			show_exc_info(self, ex)


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
				#Была выбрана группа элементов более 1-го				
				uow = self.active_repo.create_unit_of_work()
				try:
					sel_items = []
					for row in rows:
						#Я понимаю, что это жутко неоптимально, но пока что пусть будет так.
						#Выполняется отдельный SQL запрос (и не один...) для каждого из выбранных элементов
						#Потом надо бы исправить (хотя бы теги/поля/датарефы извлекать по join-стратегии
						id = self.model.items[row].id
						sel_items.append(uow.get_item(id))
					dlg = ItemsDialog(self, sel_items, DialogMode.EDIT)
					if dlg.exec_():						
						thread = UpdateGroupOfItemsThread(self, self.active_repo, sel_items)
						self.connect(thread, QtCore.SIGNAL("exception"), lambda msg: raise_exc(msg))
												
						#TODO Тут надо отображать WaitDialog
						wd = WaitDialog(self)
						self.connect(thread, QtCore.SIGNAL("finished"), wd.reject)
						self.connect(thread, QtCore.SIGNAL("exception"), wd.exception)
						self.connect(thread, QtCore.SIGNAL("progress"), wd.set_progress)
											
						thread.start()
						thread.wait(1000)
						if thread.isRunning():
							wd.exec_()
						
				finally:
					uow.close()
					
			else:
				#Был выбран ровно 1 элемент
				item_id = self.model.items[rows.pop()].id
				uow = self.active_repo.create_unit_of_work()
				try:
					item = uow.get_item(item_id)
					item_dialog = ItemDialog(item, self, DialogMode.EDIT)
					if item_dialog.exec_():
						uow.update_existing_item(item_dialog.item, self.active_user.login)						
				finally:
					uow.close()					
			
		except Exception as ex:
			show_exc_info(self, ex)
		else:
			self.ui.statusbar.showMessage(self.tr("Operation completed."), 5000)
	
	def action_template(self):
		try:
			pass
		except Exception as ex:
			show_exc_info(self, ex)
		else:
			self.ui.statusbar.showMessage(self.tr("Operation completed."), 5000)
			


class ImageThumbDelegate(QtGui.QStyledItemDelegate):
	'''Делегат, для отображения миниатюры графического файла в таблице элементов
	хранилища.'''
	def sizeHint(self, option, index):
		pixmap = index.data(QtCore.Qt.UserRole)
		if pixmap:
			return pixmap.size()
		else:
			return super(ImageThumbDelegate, self).sizeHint(option, index) #Работает в PyQt начиная с 4.8.1			
			

	def paint(self, painter, option, index):
		pixmap = index.data(QtCore.Qt.UserRole)
		if pixmap:
			painter.drawPixmap(option.rect.topLeft(), pixmap)
			#painter.drawPixmap(option.rect, pixmap)
		else:
			super(ImageThumbDelegate, self).paint(painter, option, index) #Работает в PyQt начиная с 4.8.1
			#QtGui.QStyledItemDelegate.paint(self, painter, option, index) #Для PyQt 4.7.3 надо так
	

class RepoItemTableModel(QtCore.QAbstractTableModel):
	'''Модель таблицы, отображающей элементы хранилища.'''
	
	ID = 0
	TITLE = 1
	IMAGE_THUMB = 2
	LIST_OF_TAGS = 3
	
	def __init__(self, repo):
		super(RepoItemTableModel, self).__init__()
		self.repo = repo
		self.items = []
		self.thumbs = dict()
		
	def query(self, query_text):
		'''Выполняет извлечение элементов из хранилища.'''
		
		if query_text is None or query_text.strip()=="":
			#Если запрос пустой, тогда извлекаем элементы не имеющие тегов
			uow = self.repo.create_unit_of_work()
			try:
				self.items = uow.get_untagged_items()
				self.reset()
			finally:
				uow.close()
		else:

			uow = self.repo.create_unit_of_work()
			try:
				tree = query_parser.parse(query_text)
				sql = tree.interpret()
				self.items = uow.query_items_by_sql(sql)
				self.reset()
			finally:
				uow.close()
	
	def rowCount(self, index=QtCore.QModelIndex()):
		return len(self.items)
	
	def columnCount(self, index=QtCore.QModelIndex()):
		return 4
	
	def headerData(self, section, orientation, role=Qt.DisplayRole):
		if orientation == Qt.Horizontal:
			if role == Qt.DisplayRole:
				if section == self.ID:
					return self.tr("Id")
				elif section == self.TITLE:
					return self.tr("Title")
				elif section == self.IMAGE_THUMB:
					return self.tr("Thumbnail")
				elif section == self.LIST_OF_TAGS:
					return self.tr("Tags")
			else:
				return None
		elif orientation == Qt.Vertical and role == Qt.DisplayRole:
			return section+1
		else:
			return None

	
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
			
			elif column == self.LIST_OF_TAGS:
				return item.get_list_of_tags()

		#Данная роль используется для отображения миниатюр графических файлов
		elif role == QtCore.Qt.UserRole:
			if column == self.IMAGE_THUMB and item.data_ref is not None:
				if self.thumbs.get(item.data_ref.id):
					#Если в ОП уже загружена миниатюра
					return self.thumbs.get(item.data_ref.id)
				
				elif item.data_ref.is_image():
					#Загружаем изображение в ОП и масштабируем его до размера миниатюры
					image = QtGui.QImage(self.repo.base_path + os.sep + item.data_ref.url)
					pixmap = QtGui.QPixmap.fromImage(image)
					if (pixmap.height() > pixmap.width()):
						pixmap = pixmap.scaledToHeight(\
                        int(UserConfig().get("thumbnails.size", consts.THUMBNAIL_DEFAULT_SIZE)))
					else:
						pixmap = pixmap.scaledToWidth(\
                        int(UserConfig().get("thumbnails.size", consts.THUMBNAIL_DEFAULT_SIZE)))
					
					#Запоминаем в ОП
					self.thumbs[item.data_ref.id] = pixmap
					
					#TODO Надо бы еще сохранять миниатюру в БД..
					#Потому, что если результат запроса будет содержать много элементов (графических файлов)
					#то будет жутко тормозить каждый раз
					
					#Тут бы отображать диалог ожидания, если картинок много...
					return pixmap
		

		elif role == QtCore.Qt.TextAlignmentRole:
			if column == self.ID:
				return int(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
			elif column == self.TITLE:
				return int(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
		
		
		#Во всех остальных случаях возвращаем None	
		return None
		
		


if __name__ == '__main__':
	
	print("pyqt_version = {}".format(QtCore.PYQT_VERSION_STR))
	print("qt_version = {}".format(QtCore.QT_VERSION_STR))
	
	app = QtGui.QApplication(sys.argv)
	
	#TODO Сделать выбор языка либо через конфиг файл reggata.conf, либо через Меню->Опции->Язык
	qtr = QtCore.QTranslator()
	if qtr.load("reggata_ru.qm", ".."):
		app.installTranslator(qtr)
	else:
		print("Cannot find translation files.")
	
	form = MainWindow()
	form.show()
	app.exec_()
