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
from repo_mgr import RepoMgr, UnitOfWork, BackgrThread, UpdateGroupOfItemsThread, CreateGroupIfItemsThread, DeleteGroupOfItemsThread, ThumbnailBuilderThread,\
    ItemIntegrityCheckerThread, ItemIntegrityFixerThread
from helpers import tr, show_exc_info, DialogMode, scale_value, is_none_or_empty,\
    WaitDialog, raise_exc, format_exc_info
from db_schema import Base, User, Item, DataRef, Tag, Field, Item_Field
from user_config import UserConfig
from user_dialog import UserDialog
from exceptions import LoginError, MsgException, CannotOpenRepoError
from parsers import query_parser
from tag_cloud import TagCloud
import consts
from items_dialog import ItemsDialog
from ext_app_mgr import ExtAppMgr
import helpers
import time
from image_viewer import ImageViewer
import traceback
import ui_aboutdialog
from integrity_fixer import HistoryRecNotFoundFixer, FileHashMismatchFixer,\
    FileNotFoundFixer
import math
from file_browser import FileBrowser, FileBrowserTableModel




#TODO Добавить поиск и отображение объектов DataRef, не привязанных ни к одному Item-у
#TODO Реализовать до конца грамматику языка запросов (прежде всего фильтрацию по директориям и пользователям)
#TODO Сделать функции экспорта результатов поиска во внешнюю директорию
#TODO Сделать проект механизма клонирования/синхронизации хранилищ
#TODO Сделать возможность привязывать несколько файлов к одному Item-у при помощи архивирования их на лету (при помощи zip, например)
#TODO Сделать новый тип объекта DataRef для сохранения ссылок на директории. Тогда можно будет привязывать теги и поля к директориям внутри хранилища. Надо еще подумать, стоит ли такое реализовывать или нет.
#TODO Довести до ума встроенный просмотрщик графических файлов.
#TODO Сделать всплывающие подсказки на элементах GUI
#TODO Если запрос возвращает очень много элементов, и указан limit. То нельзя передать ВСЕ элементы в просмотрщик изображений, передаются только отображенные limit штук. 
#TODO Implement searching items by Item.title attribute
#TODO Implement searching all items inside one physical directory
#TODO Implement some kind of tool to browse repository by physical file path, showing for each file it's tags

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
        
        #Это замок, который нужен для синхронизации доступа к списку элементов (результатов поиска)
        self.items_lock = QtCore.QReadWriteLock()
        
        #Контекстное меню
        self.menu = QtGui.QMenu()
        self.menu.addAction(self.ui.action_item_view)
        self.menu.addAction(self.ui.action_item_view_m3u)
        self.menu.addAction(self.ui.action_item_view_image_viewer)
        self.menu.addSeparator()
        self.menu.addAction(self.ui.action_item_edit)
        self.menu.addAction(self.ui.action_item_rebuild_thumbnail)
        self.menu.addSeparator()        
        self.menu.addAction(self.ui.action_item_delete)
        self.menu.addSeparator()
        self.menu.addAction(self.ui.action_item_check_integrity)
        self.menu.addMenu(self.ui.menuFix_integrity_errors)        
        #Добавляем его к таблице 
        self.ui.tableView_items.setContextMenuPolicy(Qt.CustomContextMenu)
        self.connect(self.ui.tableView_items, QtCore.SIGNAL("customContextMenuRequested(const QPoint &)"), self.showContextMenu)
        
                
        self.connect(self.ui.action_repo_create, QtCore.SIGNAL("triggered()"), self.action_repo_create)
        self.connect(self.ui.action_repo_close, QtCore.SIGNAL("triggered()"), self.action_repo_close)
        self.connect(self.ui.action_repo_open, QtCore.SIGNAL("triggered()"), self.action_repo_open)
        
        self.connect(self.ui.action_user_create, QtCore.SIGNAL("triggered()"), self.action_user_create)
        self.connect(self.ui.action_user_login, QtCore.SIGNAL("triggered()"), self.action_user_login)
        self.connect(self.ui.action_user_logout, QtCore.SIGNAL("triggered()"), self.action_user_logout)
        self.connect(self.ui.action_user_change_pass, QtCore.SIGNAL("triggered()"), self.action_user_change_pass)
        
        self.connect(self.ui.action_item_add, QtCore.SIGNAL("triggered()"), self.action_item_add)
        self.connect(self.ui.action_item_edit, QtCore.SIGNAL("triggered()"), self.action_item_edit)
        self.connect(self.ui.action_item_rebuild_thumbnail, QtCore.SIGNAL("triggered()"), self.action_item_rebuild_thumbnail)
        self.connect(self.ui.action_item_add_many, QtCore.SIGNAL("triggered()"), self.action_item_add_many)
        self.connect(self.ui.action_item_add_many_rec, QtCore.SIGNAL("triggered()"), self.action_item_add_many_rec)
        self.connect(self.ui.action_item_view, QtCore.SIGNAL("triggered()"), self.action_item_view)
        self.connect(self.ui.action_item_view_image_viewer, QtCore.SIGNAL("triggered()"), self.action_item_view_image_viewer)
        #self.connect(self.ui.tableView_items, QtCore.SIGNAL("doubleClicked(QModelIndex)"), self.action_item_view)
        self.connect(self.ui.action_item_delete, QtCore.SIGNAL("triggered()"), self.action_item_delete)
        self.connect(self.ui.action_item_view_m3u, QtCore.SIGNAL("triggered()"), self.action_item_view_m3u) 
        self.connect(self.ui.action_item_check_integrity, QtCore.SIGNAL("triggered()"), self.action_item_check_integrity)
        self.connect(self.ui.action_item_fix_history_rec_error, QtCore.SIGNAL("triggered()"), self.action_item_fix_history_rec_error)
        self.connect(self.ui.action_item_fix_hash_error, QtCore.SIGNAL("triggered()"), self.action_item_fix_hash_error)
        self.connect(self.ui.action_item_update_file_hash, QtCore.SIGNAL("triggered()"), self.action_item_update_file_hash)
        self.connect(self.ui.action_fix_file_not_found_try_find, QtCore.SIGNAL("triggered()"), self.action_fix_file_not_found_try_find)
        self.connect(self.ui.action_fix_file_not_found_delete, QtCore.SIGNAL("triggered()"), self.action_fix_file_not_found_delete)
        self.connect(self.ui.action_fix_file_not_found_try_find_else_delete, QtCore.SIGNAL("triggered()"), self.action_fix_file_not_found_try_find_else_delete)
        
        
        self.connect(self.ui.action_help_about, QtCore.SIGNAL("triggered()"), self.action_help_about)
        
        self.connect(self.ui.pushButton_query_exec, QtCore.SIGNAL("clicked()"), self.query_exec)
        self.connect(self.ui.lineEdit_query, QtCore.SIGNAL("returnPressed()"), self.ui.pushButton_query_exec.click)
        self.connect(self.ui.pushButton_query_reset, QtCore.SIGNAL("clicked()"), self.query_reset)
        
        #Initialization of limit and page spinboxes 
        self.ui.spinBox_limit.setValue(int(UserConfig().get("spinBox_limit.value", 0)))
        self.ui.spinBox_limit.setSingleStep(int(UserConfig().get("spinBox_limit.step", 5)))
        self.connect(self.ui.spinBox_limit, QtCore.SIGNAL("valueChanged(int)"), self.query_exec)
        self.connect(self.ui.spinBox_limit, QtCore.SIGNAL("valueChanged(int)"), lambda: UserConfig().store("spinBox_limit.value", self.ui.spinBox_limit.value()))
        self.connect(self.ui.spinBox_limit, QtCore.SIGNAL("valueChanged(int)"), lambda val: self.ui.spinBox_page.setEnabled(val > 0))
        self.connect(self.ui.spinBox_page, QtCore.SIGNAL("valueChanged(int)"), self.query_exec)
        self.ui.spinBox_page.setEnabled(self.ui.spinBox_limit.value() > 0)


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
        
        #self.connect(self.ui.lineEdit_query, QtCore.SIGNAL("textEdited(QString)"), self.reset_tag_cloud)
        
        #Add file browser
        self.ui.file_browser = FileBrowser(self)
        self.ui.dockWidget_file_browser = QtGui.QDockWidget(self)
        self.ui.dockWidget_file_browser.setWidget(self.ui.file_browser)        
        self.addDockWidget(QtCore.Qt.DockWidgetArea(4), self.ui.dockWidget_file_browser)
        
        #Открываем последнее хранилище, с которым работал пользователь
        try:
            tmp = UserConfig()["recent_repo.base_path"]
            self.active_repo = RepoMgr(tmp)
            self._login_recent_user()
        except CannotOpenRepoError:
            self.ui.statusbar.showMessage(self.tr("Cannot open recent repository."), 5000)
            self.active_repo = None
        except LoginError:
            self.ui.statusbar.showMessage(self.tr("Cannot login recent repository."), 5000)
            self.active_user = None
        except Exception as ex:
            self.ui.statusbar.showMessage(self.tr("Cannot open/login recent repository."), 5000)
        
        
        
        #Tuning table cell rendering        
        self.ui.tableView_items.setItemDelegateForColumn(RepoItemTableModel.TITLE, HTMLDelegate(self))
        self.ui.tableView_items.setItemDelegateForColumn(RepoItemTableModel.IMAGE_THUMB, ImageThumbDelegate(self))                 
        self.ui.tableView_items.setItemDelegateForColumn(RepoItemTableModel.RATING, RatingDelegate(self))
        
        self.ui.tableView_items.setSortingEnabled(True)
        
        
                
        
        #Ширина колонок в таблице
        self.ui.tableView_items.setColumnWidth(RepoItemTableModel.ID, int(UserConfig().get("items_table.ID.width", 50)))
        self.ui.tableView_items.setColumnWidth(RepoItemTableModel.TITLE, int(UserConfig().get("items_table.TITLE.width", 250)))
        self.ui.tableView_items.setColumnWidth(RepoItemTableModel.IMAGE_THUMB, int(UserConfig().get("thumbnail_size", consts.THUMBNAIL_DEFAULT_SIZE)))
        self.ui.tableView_items.setColumnWidth(RepoItemTableModel.LIST_OF_TAGS, int(UserConfig().get("items_table.LIST_OF_TAGS.width", 50)))
        self.ui.tableView_items.setColumnWidth(RepoItemTableModel.STATE, int(UserConfig().get("items_table.STATE.width", 50)))
        self.ui.tableView_items.setColumnWidth(RepoItemTableModel.RATING, int(UserConfig().get("items_table.RATING.width", 50)))
        self.connect(self.ui.tableView_items.horizontalHeader(), QtCore.SIGNAL("sectionResized(int, int, int)"), self._table_columns_resized)
        
        
        #Для старых версий PyQt задаем его для всей таблицы:
#        self.ui.tableView_items.setItemDelegate(ImageThumbDelegate())
        
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
        self.ui.tag_cloud.hint_height = int(UserConfig().get("tag_cloud.height", 100))
        self.ui.tag_cloud.hint_width = int(UserConfig().get("tag_cloud.width", 100))
        self.connect(self.ui.tag_cloud, QtCore.SIGNAL("maySaveSize"), self.save_main_window_state)
        dock_area = int(UserConfig().get("tag_cloud.dock_area", QtCore.Qt.TopDockWidgetArea))
        self.removeDockWidget(self.ui.dockWidget_tag_cloud)
        self.addDockWidget(dock_area if dock_area != Qt.NoDockWidgetArea else QtCore.Qt.TopDockWidgetArea, self.ui.dockWidget_tag_cloud)
        self.ui.dockWidget_tag_cloud.show()

    def _table_columns_resized(self, col, old_size, new_size):
        '''Обработчик события, которое возникает, когда изменяется ширина колонок таблицы.'''
        self.save_state_timer.start(1000)
    
    def _resize_row_to_contents(self, top_left, bottom_right):
        '''Обработчик сигнала, который посылает модель RepoItemTableModel, когда просит обновить 
        часть ячеек таблицы. Данный обработчик подгоняет высоту строк под новое содержимое.'''        
        if top_left.row() == bottom_right.row():
            self.ui.tableView_items.resizeRowToContents(top_left.row())
            print("resizing row={}".format(top_left.row()))
        elif top_left.row() < bottom_right.row():
            for row in range(top_left.row(), bottom_right.row()):
                self.ui.tableView_items.resizeRowToContents(row)
                print("resizing row={}".format(row))

    def event(self, e):
        #Информация о нажатии Control-а передается облаку тегов
        if e.type() == QtCore.QEvent.KeyPress and e.key() == Qt.Key_Control:
            self.ui.tag_cloud.control_pressed = True
        elif e.type() == QtCore.QEvent.KeyRelease and e.key() == Qt.Key_Control:
            self.ui.tag_cloud.control_pressed = False
        return super(MainWindow, self).event(e)

    def showContextMenu(self, pos):
        self.menu.exec_(self.ui.tableView_items.mapToGlobal(pos))

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
        UserConfig().storeAll({"tag_cloud.width":self.ui.tag_cloud.hint_width, "tag_cloud.height":self.ui.tag_cloud.hint_height})
        
        #Расположение облака тегов
        UserConfig().store("tag_cloud.dock_area", str(self.dockWidgetArea(self.ui.dockWidget_tag_cloud)))
        
        #Ширина колонок таблицы
        width_id = self.ui.tableView_items.columnWidth(RepoItemTableModel.ID)
        width_title = self.ui.tableView_items.columnWidth(RepoItemTableModel.TITLE)
        width_list_of_tags = self.ui.tableView_items.columnWidth(RepoItemTableModel.LIST_OF_TAGS)
        width_state = self.ui.tableView_items.columnWidth(RepoItemTableModel.STATE)
        width_rating = self.ui.tableView_items.columnWidth(RepoItemTableModel.RATING)
        if width_id > 0:
            UserConfig().store("items_table.ID.width", str(width_id))
        if width_title > 0:
            UserConfig().store("items_table.TITLE.width", str(width_title))
        if width_list_of_tags > 0:
            UserConfig().store("items_table.LIST_OF_TAGS.width", str(width_list_of_tags))
        if width_state > 0:
            UserConfig().store("items_table.STATE.width", str(width_state))
        if width_rating > 0:
            UserConfig().store("items_table.RATING.width", str(width_rating))
            
        
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
            limit = self.ui.spinBox_limit.value()
            page = self.ui.spinBox_page.value()
            self.model.query(query_text, limit, page)
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
        
        
        if user is not None:
            #Добавляем в облако новый логин
            self.ui.tag_cloud.add_user(user.login)
        
            #Tell to table model that current active user has changed
            if self.model is not None and isinstance(self.model, RepoItemTableModel):
                self.model.user_login = user.login
        
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
    
        try:
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
                self.model = RepoItemTableModel(repo, self.items_lock, self.active_user.login if self.active_user is not None else None)
                self.ui.tableView_items.setModel(self.model)
                self.connect(self.model, QtCore.SIGNAL("modelReset()"), self.ui.tableView_items.resizeRowsToContents)
                #self.connect(self.model, QtCore.SIGNAL("modelReset()"), self.ui.tableView_items.resizeColumnsToContents)
                self.connect(self.model, QtCore.SIGNAL("dataChanged(const QModelIndex&, const QModelIndex&)"), self._resize_row_to_contents)
                
                self.ui.file_browser.root_path = repo.base_path
                
            else:
                self.ui.label_repo.setText("")
                self.model = None
                self.ui.tableView_items.setModel(None)
        except Exception as ex:
            raise CannotOpenRepoError(str(ex), ex)
                
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
    

    def action_item_delete(self):
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
            
            #TODO Нужно сделать свой диалог, содержащий checkbox "Удалить связанные физические файлы"
            mb = QtGui.QMessageBox()
            mb.setText(self.tr("Do you really want to delete {} selected file(s)?").format(len(rows)))
            mb.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            if mb.exec_() == QtGui.QMessageBox.Yes:
                #Получаем id всех объектов, которые будем удалять
                item_ids = []
                for row in rows:
                    item_ids.append(self.model.items[row].id)
                
                thread = DeleteGroupOfItemsThread(self, self.active_repo, item_ids, self.active_user.login)
                self.connect(thread, QtCore.SIGNAL("exception"), lambda msg: raise_exc(msg))
                                        
                wd = WaitDialog(self)
                self.connect(thread, QtCore.SIGNAL("finished"), wd.reject)
                self.connect(thread, QtCore.SIGNAL("exception"), wd.exception)
                self.connect(thread, QtCore.SIGNAL("progress"), wd.set_progress)
                
                thread.start()
                thread.wait(1000)
                if thread.isRunning():
                    wd.exec_()
                    
                if thread.errors > 0:
                    mb = helpers.MyMessageBox(self)
                    mb.setWindowTitle(tr("Information"))
                    mb.setText(self.tr("There were {0} errors.").format(thread.errors))                    
                    mb.setDetailedText(thread.detailed_message)
                    mb.exec_()
                
            else:
                self.ui.statusbar.showMessage(self.tr("Cancelled."), 5000)
            
        except Exception as ex:
            show_exc_info(self, ex)
        else:
            self.ui.statusbar.showMessage(self.tr("Operation completed."), 5000)
            self.query_exec()
            self.ui.tag_cloud.refresh()
            
    def action_item_view(self):
        try:
            sel_indexes = self.ui.tableView_items.selectionModel().selectedIndexes()
            if len(sel_indexes) != 1:
                raise MsgException(self.tr("Select one item, please."))
            
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

    def action_item_view_image_viewer(self):
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
            
            abs_paths = []
            for row in rows:
                abs_paths.append(os.path.join(self.active_repo.base_path, self.model.items[row].data_ref.url))
                
                                                        
            iv = ImageViewer(self, abs_paths)
            iv.setWindowModality(Qt.WindowModal)
            iv.show()
            
            
        except Exception as ex:
            show_exc_info(self, ex)
        else:
            self.ui.statusbar.showMessage(self.tr("Operation completed."), 5000)

    def action_fix_file_not_found_try_find(self):
        strategy = {Item.ERROR_FILE_NOT_FOUND: FileNotFoundFixer.TRY_FIND}
        self._fix_integrity_error(strategy)
        
    def action_fix_file_not_found_delete(self):
        strategy = {Item.ERROR_FILE_NOT_FOUND: FileNotFoundFixer.DELETE}
        self._fix_integrity_error(strategy)
        
    def action_fix_file_not_found_try_find_else_delete(self):
        strategy = {Item.ERROR_FILE_NOT_FOUND: FileNotFoundFixer.TRY_FIND_ELSE_DELETE}
        self._fix_integrity_error(strategy)

    def action_item_update_file_hash(self):
        strategy = {Item.ERROR_FILE_HASH_MISMATCH: FileHashMismatchFixer.UPDATE_HASH}
        self._fix_integrity_error(strategy)

    def action_item_fix_hash_error(self):
        strategy = {Item.ERROR_FILE_HASH_MISMATCH: FileHashMismatchFixer.TRY_FIND_FILE}
        self._fix_integrity_error(strategy)
    
    def action_item_fix_history_rec_error(self):
        strategy = {Item.ERROR_HISTORY_REC_NOT_FOUND: HistoryRecNotFoundFixer.TRY_PROCEED_ELSE_RENEW}
        self._fix_integrity_error(strategy)
    
    def _fix_integrity_error(self, strategy):
        
        def refresh(percent, row):
            self.ui.statusbar.showMessage(self.tr("Integrity fix {0}%").format(percent))
            self.model.reset_single_row(row)
            QtCore.QCoreApplication.processEvents()
        
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
            
            items = []
            for row in rows:
                #Нужно в элементе сохранить номер строки таблицы, откуда взят элемент
                self.model.items[row].table_row = row
                items.append(self.model.items[row])
                        
            thread = ItemIntegrityFixerThread(self, self.active_repo, items, self.items_lock, strategy, self.active_user.login)
            
            self.connect(thread, QtCore.SIGNAL("exception"), lambda exc_info: show_exc_info(self, exc_info[1], details=format_exc_info(*exc_info)))
            self.connect(thread, QtCore.SIGNAL("finished"), lambda: self.ui.statusbar.showMessage(self.tr("Integrity fixing is done.")))
            self.connect(thread, QtCore.SIGNAL("progress"), lambda percents, row: refresh(percents, row))
            thread.start()
            
        except Exception as ex:
            show_exc_info(self, ex)
        else:
            pass

    
        
#        def refresh(percent, row):
#            self.ui.statusbar.showMessage(self.tr("Integrity fix {0}%").format(percent))
#            self.model.reset_single_row(row)
#            QtCore.QCoreApplication.processEvents()
#        
#        try:
#            if self.active_repo is None:
#                raise MsgException(self.tr("Open a repository first."))
#            
#            if self.active_user is None:
#                raise MsgException(self.tr("Login to a repository first."))
#            
#            #Нужно множество, т.к. в результате selectedIndexes() могут быть дубликаты
#            rows = set()
#            for idx in self.ui.tableView_items.selectionModel().selectedIndexes():
#                rows.add(idx.row())
#            
#            if len(rows) == 0:
#                raise MsgException(self.tr("There are no selected items."))
#            
#            items = []
#            for row in rows:
#                #Нужно в элементе сохранить номер строки таблицы, откуда взят элемент
#                self.model.items[row].table_row = row
#                items.append(self.model.items[row])
#            
#            strategy = {Item.ERROR_HISTORY_REC_NOT_FOUND: HistoryRecNotFoundFixer.TRY_PROCEED_ELSE_RENEW}
#            thread = ItemIntegrityFixerThread(self, self.active_repo, items, self.items_lock, strategy, self.active_user.login)
#            
#            self.connect(thread, QtCore.SIGNAL("exception"), lambda exc_info: show_exc_info(self, exc_info[1], details=format_exc_info(*exc_info)))
#            self.connect(thread, QtCore.SIGNAL("finished"), lambda: self.ui.statusbar.showMessage(self.tr("Integrity fixing is done.")))
#            self.connect(thread, QtCore.SIGNAL("progress"), lambda percents, row: refresh(percents, row))
#            thread.start()
#            
#        except Exception as ex:
#            show_exc_info(self, ex)
#        else:
#            pass

    def action_item_check_integrity(self):
        
        def refresh(percent, row):
            self.ui.statusbar.showMessage(self.tr("Integrity check {0}%").format(percent))            
            self.model.reset_single_row(row)
            QtCore.QCoreApplication.processEvents()
        
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
            
            items = []
            for row in rows:
                #Нужно в элементе сохранить номер строки таблицы, откуда взят элемент
                self.model.items[row].table_row = row
                items.append(self.model.items[row])
             
            thread = ItemIntegrityCheckerThread(self, self.active_repo, items, self.items_lock)
            self.connect(thread, QtCore.SIGNAL("exception"), lambda msg: raise_exc(msg))
            self.connect(thread, QtCore.SIGNAL("finished"), lambda error_count: self.ui.statusbar.showMessage(self.tr("Integrity check is done. {0} Items with errors.").format(error_count)))            
            self.connect(thread, QtCore.SIGNAL("progress"), lambda percents, row: refresh(percents, row))
            thread.start()
            
        except Exception as ex:
            show_exc_info(self, ex)
        else:
            pass


    def action_item_view_m3u(self):
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
            
            tmp_dir = UserConfig().get("tmp_dir", consts.DEFAULT_TMP_DIR)
            if not os.path.exists(tmp_dir):
                os.makedirs(tmp_dir)
            m3u_filename = str(os.getpid()) + self.active_user.login + str(time.time()) + ".m3u"
            m3u_file = open(os.path.join(tmp_dir, m3u_filename), "wt")
            for row in rows:
                m3u_file.write(os.path.join(self.active_repo.base_path, self.model.items[row].data_ref.url) + os.linesep)                                            
            m3u_file.close()
            
            eam = ExtAppMgr()
            eam.invoke(os.path.join(tmp_dir, m3u_filename))
            
        except Exception as ex:
            show_exc_info(self, ex)
        else:
            self.ui.statusbar.showMessage(self.tr("Operation completed."), 5000)


    def action_item_add_many_rec(self):
        '''Добавление всех файлов, содержащихся в одной директории, в виде 
        отдельных элементов в хранилище. При этом ко всем добавляемым
        файлам привязываются одинаковые теги и поля. 
        Расположение файлов в хранилище будет соответствовать их расположению в 
        исходной директории.
        Название title каждого элемента будет совпадать с
        именем добавляемого файла.'''
        try:
            if self.active_repo is None:
                raise MsgException(self.tr("Open a repository first."))
            
            if self.active_user is None:
                raise MsgException(self.tr("Login to a repository first."))
            
            
            dir = QtGui.QFileDialog.getExistingDirectory(self, self.tr("Select one directory"))
            if not dir:
                raise MsgException(self.tr("Directory is not chosen. Operation cancelled."))
            
            items = []
            for root, dirs, files in os.walk(dir):
                for file in files:
#                    print(os.path.relpath(root, dir) + " FILE: " + file)
                    abs_file = os.path.join(root, file)
                    item = Item(user_login=self.active_user.login)
                    item.title = file
                    item.data_ref = DataRef(url=abs_file, type=DataRef.FILE)
                    item.data_ref.dst_subpath = os.path.relpath(root, dir)
                    items.append(item)
            
            #Открываем диалог для ввода информации о тегах и полях
            d = ItemsDialog(self, items, DialogMode.CREATE, same_dst_path=False)
            if d.exec_():
                
                thread = CreateGroupIfItemsThread(self, self.active_repo, items)
                self.connect(thread, QtCore.SIGNAL("exception"), lambda msg: raise_exc(msg))
                                        
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
            self.query_exec()
            
            
        
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
            self.query_exec()
        
        
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
            self.query_exec()
    
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


    
    def action_item_rebuild_thumbnail(self):
        
        def refresh(percent, row):
            self.ui.statusbar.showMessage(self.tr("Rebuilding thumbnails ({0}%)").format(percent))            
            self.model.reset_single_row(row)
            QtCore.QCoreApplication.processEvents()
        
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
            
            print("selected rows: {}".format(rows))
            
            
            uow = self.active_repo.create_unit_of_work()
            try:
                items = []
                for row in rows:
                    #Нужно в элементе сохранить номер строки таблицы, откуда взят элемент
                    self.model.items[row].table_row = row
                    items.append(self.model.items[row])
                 
                thread = ThumbnailBuilderThread(self, self.active_repo, items, self.items_lock, rebuild=True)
                self.connect(thread, QtCore.SIGNAL("exception"), lambda exc_info: helpers.show_exc_info(self, exc_info[1], details=format_exc_info(*exc_info)))
                self.connect(thread, QtCore.SIGNAL("finished"), lambda: self.ui.statusbar.showMessage(self.tr("Rebuild thumbnails is done.")))            
                self.connect(thread, QtCore.SIGNAL("progress"), lambda percents, row: refresh(percents, row))
                thread.start()
                    
            finally:
                uow.close()
                    
                                
            
        except Exception as ex:
            show_exc_info(self, ex)
        else:
            pass
            
            

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
            self.query_exec()
            self.ui.tag_cloud.refresh()
    
    def action_help_about(self):
        try:
            ad = AboutDialog(self)
            ad.exec_()
            
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
    def __init__(self, parent=None):
        super(ImageThumbDelegate, self).__init__(parent)
        
    def sizeHint(self, option, index):
        pixmap = index.data(QtCore.Qt.UserRole)
        if pixmap:
            return pixmap.size()
        else:
            return super(ImageThumbDelegate, self).sizeHint(option, index) #Работает в PyQt начиная с 4.8.1            
            

    def paint(self, painter, option, index):
        
        pixmap = index.data(QtCore.Qt.UserRole)
        if pixmap is not None and not pixmap.isNull():
            painter.drawPixmap(option.rect.topLeft(), pixmap)
            #painter.drawPixmap(option.rect, pixmap)
        else:
            super(ImageThumbDelegate, self).paint(painter, option, index) #Работает в PyQt начиная с 4.8.1
            #QtGui.QStyledItemDelegate.paint(self, painter, option, index) #Для PyQt 4.7.3 надо так

class RatingDelegate(QtGui.QStyledItemDelegate):
    '''An ItemDelegate for displaying Rating of items. Rating value is stored 
    in a regular field with name consts.RATING_FIELD.'''
    
    def __init__(self, parent=None, r=10):
        super(RatingDelegate, self).__init__(parent)
        
        palette = QtGui.QApplication.palette()
        
        self.r = r
        self.star = QtGui.QPixmap(2*r, 2*r)
        self.star.fill(QtGui.QColor(255, 255, 255, 0)) #This is an absolutely transparent color
        painter = QtGui.QPainter(self.star)
        path = QtGui.QPainterPath()
        
        
        for i in range(0, 10):
            radius = r if i % 2 == 0 else r*0.4
            if i == 0:
                path.moveTo(QtCore.QPointF(radius*math.cos(i*2*math.pi/10), radius*math.sin(i*2*math.pi/10)))
            else:
                path.lineTo(QtCore.QPointF(radius*math.cos(i*2*math.pi/10), radius*math.sin(i*2*math.pi/10)))        
        painter.save()
        painter.translate(r, r)
        painter.setPen(palette.text().color())
        painter.setBrush(QtGui.QBrush(palette.button().color()))
        painter.drawPath(path)
        painter.restore()
        
        
        
    
    def sizeHint(self, option, index):
        return QtCore.QSize(option.rect.width(), self.r)
        #TODO should return some size?..
        #return super(RatingDelegate, self).sizeHint(option, index)
            

    def paint(self, painter, option, index):
        
        palette = QtGui.QApplication.palette()
        
        bg_color = palette.highlight().color() \
            if option.state & QtGui.QStyle.State_Selected \
            else palette.base().color()
        
        rating = int(index.data(QtCore.Qt.DisplayRole))
        
        #TODO Maybe max rating should be 10?
        if rating < 0:
            rating = 0
        elif rating > 5:
            rating = 5
            
        painter.save()
        painter.fillRect(option.rect, bg_color)
        painter.translate(option.rect.x(), option.rect.y())
        for i in range(0, rating):
            painter.drawPixmap(0, 0, self.star)
            painter.translate(self.star.width() + 1, 0.0)
        painter.restore()
        
    
    def createEditor(self, parent, option, index):
        
        editor = QtGui.QSpinBox(parent)
        editor.setMinimum(0)
        editor.setMaximum(5)
        return editor
    
    def setEditorData(self, editor, index):
        
        try:
            rating = int(index.data(QtCore.Qt.DisplayRole))
        except:
            rating = 0
        editor.setValue(rating)
    
    def setModelData(self, editor, model, index):
        
        model.setData(index, editor.value())
    
    def updateEditorGeometry(self, editor, option, index):
        
        editor.setGeometry(option.rect)

class HTMLDelegate(QtGui.QStyledItemDelegate):
    '''Делегат, для отображения HTML текста в таблице.'''
    def __init__(self, parent=None):
        super(HTMLDelegate, self).__init__(parent)
        self.text_edit = QtGui.QTextEdit()
        
    def sizeHint(self, option, index):
        
        raw_text = index.data(Qt.DisplayRole)
        if raw_text is not None:
            doc = QtGui.QTextDocument()
            doc.setTextWidth(option.rect.width())
            doc.setDefaultFont(option.font)
            doc.setHtml(raw_text)            
            return QtCore.QSize(doc.size().width(), doc.size().height())
        else:
            return super(HTMLDelegate, self).sizeHint(option, index) #Работает в PyQt начиная с 4.8.1
            

    def paint(self, painter, option, index):
        
        palette = QtGui.QApplication.palette()
        
        bg_color = palette.highlight().color() \
            if option.state & QtGui.QStyle.State_Selected \
            else palette.base().color()
            
        text_color = palette.highlightedText().color() \
            if option.state & QtGui.QStyle.State_Selected \
            else palette.text().color()
        
        raw_text = index.data(Qt.DisplayRole)
        if raw_text is not None:
            doc = QtGui.QTextDocument()
            doc.setTextWidth(option.rect.width())
            doc.setDefaultFont(option.font)
            doc.setHtml(raw_text)
            
            cursor = QtGui.QTextCursor(doc)
            format = QtGui.QTextCharFormat()
            format.setForeground(QtGui.QBrush(text_color))
            cursor.movePosition(QtGui.QTextCursor.Start)
            cursor.movePosition(QtGui.QTextCursor.End, QtGui.QTextCursor.KeepAnchor)
            cursor.mergeCharFormat(format)
                    
            painter.save()
            painter.fillRect(option.rect, bg_color)
            painter.translate(option.rect.x(), option.rect.y())
            doc.drawContents(painter, QtCore.QRectF(0 ,0, option.rect.width(), option.rect.height()))            
            painter.restore()
    
        else:
            super(HTMLDelegate, self).paint(painter, option, index) #Работает в PyQt начиная с 4.8.1
            


class RepoItemTableModel(QtCore.QAbstractTableModel):
    '''Модель таблицы, отображающей элементы хранилища.'''
    
    ID = 0
    TITLE = 1
    IMAGE_THUMB = 2
    LIST_OF_TAGS = 3
    STATE = 4 #Состояние элемента (в смысле целостности его данных)
    RATING = 5
    
    #TODO Should pass current active user login to __init__() !!!
    def __init__(self, repo, items_lock, user_login):
        super(RepoItemTableModel, self).__init__()
        self.repo = repo
        self.items = []
        self._user_login = user_login
        
        
        #Это поток, который генерирует миниатюры в фоне
        self.thread = None
        
        #Это замок, который нужен для синхронизации доступа к списку self.items
        self.lock = items_lock

        #This fields are required for table sorting
        self.query_text = ""
        self.limit = 0
        self.page = 1
        
        self.order_by_column = None
        self.order_dir = None


    def reset_single_row(self, row):
        topL = self.createIndex(row, self.ID)
        bottomR = self.createIndex(row, self.RATING)
        self.emit(QtCore.SIGNAL("dataChanged(const QModelIndex&, const QModelIndex&)"), topL, bottomR)

    def _set_user_login(self, user_login):
        self._user_login = user_login
        
    def _get_user_login(self):
        return self._user_login
    
    user_login = property(_get_user_login, _set_user_login, doc="Current active user login.")
    
    
    def sort(self, column, order=Qt.AscendingOrder):
        if column not in [self.ID, self.TITLE, self.RATING]:
            return
        
        self.order_by_column = column
        self.order_dir = order
                
        self.query(self.query_text, self.limit, self.page)
        
    
    def query(self, query_text, limit=0, page=1):
        '''Выполняет извлечение элементов из хранилища.'''
        
        self.query_text = query_text
        self.limit = limit
        self.page = page
        
        if self.order_dir == Qt.AscendingOrder:
            dir = "ASC"
        else:
            dir = "DESC"
        
        order_by = []        
        if self.order_by_column is not None:
            column = self.order_by_column
            if column == self.ID:
                order_by.append(("id", dir))                
            elif column == self.TITLE:
                order_by.append(("title", dir))
            #This is not exactly sorting by pure rating, but by fields and their values...
            elif column == self.RATING:
                order_by.append(("items_fields_field_id", "DESC"))
                order_by.append(("items_fields_field_value", dir))
    
        
        def reset_row(row):
            self.reset_single_row(row)
            QtCore.QCoreApplication.processEvents()
        
        uow = self.repo.create_unit_of_work()
        try:
            #Нужно остановить поток (запущенный от предыдущего запроса), если будет выполнен новый запрос (этот)
            if self.thread is not None and self.thread.isRunning():
                #Нужно остановить поток, если будет выполнен другой запрос
                self.thread.interrupt = True
                self.thread.wait(5*1000) #TODO Тут может надо ждать бесконечно?
                        
            if query_text is None or query_text.strip()=="":
                #Если запрос пустой, тогда извлекаем элементы не имеющие тегов
                self.items = uow.get_untagged_items(limit, page, order_by)
            else:
                query_tree = query_parser.parse(query_text)
                self.items = uow.query_items_by_tree(query_tree, limit, page, order_by)
            
            #Нужно запустить поток, который будет генерировать миниатюры
            self.thread = ThumbnailBuilderThread(self, self.repo, self.items, self.lock)
            self.connect(self.thread, QtCore.SIGNAL("progress"), lambda percents, row: reset_row(row))            
            self.thread.start()
                
            self.reset()
        finally:
            uow.close()
    
        
                
        
    
    def rowCount(self, index=QtCore.QModelIndex()):
        return len(self.items)
    
    def columnCount(self, index=QtCore.QModelIndex()):
        return 6
    
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
                elif section == self.STATE:
                    return self.tr("State")
                elif section == self.RATING:
                    return self.tr("Rating")
            else:
                return None
        elif orientation == Qt.Vertical and role == Qt.DisplayRole:
            return section + 1
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
                return "<b>" + item.title + "</b>" + ("<br/><font>" + item.data_ref.url + "</font>" if item.data_ref else "")
            
            elif column == self.LIST_OF_TAGS:
                return item.format_tags()
            
            elif column == self.STATE:
                try:
                    self.lock.lockForRead()
                    return Item.format_error_set_short(item.error)
                finally:
                    self.lock.unlock()
            elif column == self.RATING:
                #Should display only rating field owned by current active user
                rating_str = item.get_field_value(consts.RATING_FIELD, self.user_login)
                try:
                    rating = int(rating_str)
                except:
                    rating = 0
                return rating
        
        elif role == Qt.ToolTipRole:            
            if column == self.TITLE:
                if item.data_ref is not None:
                    s  =  str(item.data_ref.type) + ": " + item.data_ref.url
                    if  item.data_ref.type == DataRef.FILE:
                        s += os.linesep + self.tr("Checksum (hash): {}").format(item.data_ref.hash)
                        s += os.linesep + self.tr("File size: {} bytes").format(item.data_ref.size)
                        s += os.linesep + self.tr("Date hashed: {}").format(item.data_ref.date_hashed)
                    s += os.linesep + self.tr("Created by: {}").format(item.data_ref.user_login)
                    s += os.linesep + self.tr("Date created: {}").format(item.data_ref.date_created)
                    
                    
                    return s
            elif column == self.LIST_OF_TAGS:
                return item.format_field_vals()
            elif column == self.STATE:
                try:
                    self.lock.lockForRead()
                    return Item.format_error_set(item.error)
                finally:
                    self.lock.unlock()
            

        #Данная роль используется для отображения миниатюр графических файлов
        elif role == QtCore.Qt.UserRole:
            if column == self.IMAGE_THUMB and item.data_ref is not None:
                if item.data_ref.is_image():
                    pixmap = QtGui.QPixmap()
                    try:                    
                        self.lock.lockForRead()
                        if len(item.data_ref.thumbnails) > 0:
                            pixmap.loadFromData(item.data_ref.thumbnails[0].data)
                    except Exception:
                        traceback.format_exc()
                    finally:
                        self.lock.unlock()
                    return pixmap
        

        elif role == QtCore.Qt.TextAlignmentRole:
            if column == self.ID:
                return int(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            elif column == self.TITLE:
                return int(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        
        #Во всех остальных случаях возвращаем None    
        return None
    
    def flags(self, index):
        default_flags = super(RepoItemTableModel, self).flags(index)
        
        if index.column() == self.RATING:
            return Qt.ItemFlags(default_flags | QtCore.Qt.ItemIsEditable)             
        else:
            return default_flags
    
    def setData(self, index, value, role=QtCore.Qt.EditRole):
        
        if role == Qt.EditRole and index.column() == self.RATING:
            item = self.items[index.row()]
            
            #Remember old rating value
            old_value = item.get_field_value(consts.RATING_FIELD, self.user_login)
            
            if old_value == value:
                return False
            
            item.set_field_value(consts.RATING_FIELD, value, self.user_login)
            
            #Store new rating value into database
            uow = self.repo.create_unit_of_work()
            try:
                uow.update_existing_item(item, self.user_login)
                self.emit(QtCore.SIGNAL("dataChanged(const QModelIndex&, const QModelIndex&)"), index, index)
                return True
            except:
                #Restore old value
                item.set_field_value(consts.RATING_FIELD, old_value, self.user_login)
            finally:
                uow.close()
        
        return False


class AboutDialog(QtGui.QDialog):
    
    #TODO Надо как-то автоматически выводить информацию о версии Reggata
    
    def __init__(self, parent=None):
        super(AboutDialog, self).__init__(parent)
        self.ui = ui_aboutdialog.Ui_AboutDialog()
        self.ui.setupUi(self) 
        


if __name__ == '__main__':
    
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


