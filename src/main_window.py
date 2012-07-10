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
import datetime
import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui
import ui_mainwindow
from item_dialog import ItemDialog
from repo_mgr import RepoMgr
from helpers import tr, show_exc_info, DialogMode, is_none_or_empty,\
    WaitDialog, raise_exc, format_exc_info
from db_schema import User, Item, DataRef
from user_config import UserConfig
from user_dialog import UserDialog
from exceptions import LoginError, MsgException, CannotOpenRepoError
from tag_cloud import TagCloud
import consts
from items_dialog import ItemsDialog
from ext_app_mgr import ExtAppMgr
import helpers
import time
from image_viewer import ImageViewer
import ui_aboutdialog
from integrity_fixer import HistoryRecNotFoundFixer, FileHashMismatchFixer,\
    FileNotFoundFixer
from file_browser import FileBrowser, FileBrowserTableModel
from worker_threads import BackgrThread, UpdateGroupOfItemsThread, \
    CreateGroupIfItemsThread, DeleteGroupOfItemsThread, ThumbnailBuilderThread,\
    ItemIntegrityCheckerThread, ItemIntegrityFixerThread, ExportItemsThread
from items_table_dock_widget import ItemsTableDockWidget
from table_models import RepoItemTableModel


class MainWindow(QtGui.QMainWindow):
    '''
    Reggata's main window.
    '''
    
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.ui = ui_mainwindow.Ui_MainWindow()
        self.ui.setupUi(self)
        
        #Current opened (active) repository (RepoMgr object)
        self.__active_repo = None
        
        #Current logined (active) user
        self.__active_user = None
        
        #Table model for items table
        self.model = None
        
        self.items_lock = QtCore.QReadWriteLock()
        
        self.menu = self.create_items_table_context_menu()
        
        #Create ItemsTableDockWidget
        self.ui.dockWidget_items_table = ItemsTableDockWidget(self)
        self.ui.dockWidget_items_table.addContextMenu(self.menu)
        self.addDockWidget(QtCore.Qt.TopDockWidgetArea, self.ui.dockWidget_items_table)
        self.connect(self.ui.dockWidget_items_table, 
                     QtCore.SIGNAL("query_exec"), self.query_exec)
        self.connect(self.ui.dockWidget_items_table, 
                     QtCore.SIGNAL("query_reset"), self.query_reset)
        
                
        self.connect_menu_actions()

        #Creating status bar widgets
        self.ui.label_repo = QtGui.QLabel()
        self.ui.label_user = QtGui.QLabel()
        self.ui.statusbar.addPermanentWidget(QtGui.QLabel(self.tr("Repository:")))
        self.ui.statusbar.addPermanentWidget(self.ui.label_repo)
        self.ui.statusbar.addPermanentWidget(QtGui.QLabel(self.tr("User:")))
        self.ui.statusbar.addPermanentWidget(self.ui.label_user)
        
        self.setCentralWidget(None)
        
        #Items table
        self.connect(self.ui.action_tools_items_table, 
                     QtCore.SIGNAL("triggered(bool)"), 
                     lambda b: self.ui.dockWidget_items_table.setVisible(b))
        self.connect(self.ui.dockWidget_items_table, 
                     QtCore.SIGNAL("visibilityChanged(bool)"), 
                     lambda b: self.ui.action_tools_items_table.setChecked(b))

        
        #Adding tag cloud
        self.ui.tag_cloud = TagCloud(self)
        self.ui.dockWidget_tag_cloud = QtGui.QDockWidget(self.tr("Tag cloud"), self)
        self.ui.dockWidget_tag_cloud.setObjectName("dockWidget_tag_cloud")
        self.ui.dockWidget_tag_cloud.setWidget(self.ui.tag_cloud)
        self.addDockWidget(QtCore.Qt.TopDockWidgetArea, self.ui.dockWidget_tag_cloud)
        self.connect(self.ui.tag_cloud, 
                     QtCore.SIGNAL("selectedTagsChanged"), 
                     self.ui.dockWidget_items_table.selected_tags_changed)
        self.connect(self.ui.action_tools_tag_cloud, 
                     QtCore.SIGNAL("triggered(bool)"), 
                     lambda b: self.ui.dockWidget_tag_cloud.setVisible(b))
        self.connect(self.ui.dockWidget_tag_cloud, 
                     QtCore.SIGNAL("visibilityChanged(bool)"), 
                     lambda b: self.ui.action_tools_tag_cloud.setChecked(b))
                
        #Adding file browser
        self.ui.file_browser = FileBrowser(self)
        self.ui.dockWidget_file_browser = QtGui.QDockWidget(self.tr("File browser"), self)
        self.ui.dockWidget_file_browser.setObjectName("dockWidget_file_browser")
        self.ui.dockWidget_file_browser.setWidget(self.ui.file_browser)        
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.ui.dockWidget_file_browser)
        self.connect(self.ui.action_tools_file_browser, 
                     QtCore.SIGNAL("triggered(bool)"), 
                     lambda b: self.ui.dockWidget_file_browser.setVisible(b))
        self.connect(self.ui.dockWidget_file_browser, 
                     QtCore.SIGNAL("visibilityChanged(bool)"), 
                     lambda b: self.ui.action_tools_file_browser.setChecked(b))
        
        self.tabifyDockWidget(self.ui.dockWidget_file_browser, self.ui.dockWidget_items_table)        
        
        #Try to open and login recent repository with recent user login
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
                
        #Restoring columns width of items table
        self.ui.dockWidget_items_table.restore_columns_width()
        
        #Restoring columns width of file browser
        self.restore_file_browser_state()
        
        #Restoring main window size
        width = int(UserConfig().get("main_window.width", 640))
        height = int(UserConfig().get("main_window.height", 480))
        self.resize(width, height)
        
        #Restoring all dock widgets position and size
        state = UserConfig().get("main_window.state")
        if state:
            state = eval(state)
            self.restoreState(state)

    def connect_menu_actions(self):
        #MENU: Repository
        self.connect(self.ui.action_repo_create, 
                     QtCore.SIGNAL("triggered()"), self.action_repo_create)
        self.connect(self.ui.action_repo_close, 
                     QtCore.SIGNAL("triggered()"), self.action_repo_close)
        self.connect(self.ui.action_repo_open, 
                     QtCore.SIGNAL("triggered()"), self.action_repo_open)
        
        #MENU: User
        self.connect(self.ui.action_user_create, 
                     QtCore.SIGNAL("triggered()"), self.action_user_create)
        self.connect(self.ui.action_user_login, 
                     QtCore.SIGNAL("triggered()"), self.action_user_login)
        self.connect(self.ui.action_user_logout, 
                     QtCore.SIGNAL("triggered()"), self.action_user_logout)
        self.connect(self.ui.action_user_change_pass, 
                     QtCore.SIGNAL("triggered()"), self.action_user_change_pass)
        
        #MENU: Item
        self.connect(self.ui.action_item_add, 
                     QtCore.SIGNAL("triggered()"), self.action_item_add)
        self.connect(self.ui.action_item_add_many, 
                     QtCore.SIGNAL("triggered()"), self.action_item_add_many)
        self.connect(self.ui.action_item_add_many_rec, 
                     QtCore.SIGNAL("triggered()"), self.action_item_add_many_rec)
        #SEPARATOR
        self.connect(self.ui.action_item_edit, 
                     QtCore.SIGNAL("triggered()"), self.action_item_edit)
        self.connect(self.ui.action_item_rebuild_thumbnail, 
                     QtCore.SIGNAL("triggered()"), self.action_item_rebuild_thumbnail)
        #SEPARATOR
        self.connect(self.ui.action_item_delete, 
                     QtCore.SIGNAL("triggered()"), self.action_item_delete)
        #SEPARATOR
        self.connect(self.ui.action_item_view, 
                     QtCore.SIGNAL("triggered()"), self.action_item_view)
        self.connect(self.ui.action_item_view_image_viewer, 
                     QtCore.SIGNAL("triggered()"), self.action_item_view_image_viewer)        
        self.connect(self.ui.action_item_view_m3u, 
                     QtCore.SIGNAL("triggered()"), self.action_item_view_m3u)
        self.connect(self.ui.action_item_to_external_filemanager, 
                     QtCore.SIGNAL("triggered()"), self.action_item_to_external_filemanager)
        self.connect(self.ui.action_export_selected_items, 
                     QtCore.SIGNAL("triggered()"), self.action_export_selected_items)
        self.connect(self.ui.action_export_items_file_paths, 
                     QtCore.SIGNAL("triggered()"), self.action_export_items_file_paths)
        #SEPARATOR
        self.connect(self.ui.action_item_check_integrity, 
                     QtCore.SIGNAL("triggered()"), self.action_item_check_integrity)
        self.connect(self.ui.action_item_fix_hash_error, 
                     QtCore.SIGNAL("triggered()"), self.action_item_fix_hash_error)
        self.connect(self.ui.action_item_update_file_hash, 
                     QtCore.SIGNAL("triggered()"), self.action_item_update_file_hash)
        self.connect(self.ui.action_item_fix_history_rec_error, 
                     QtCore.SIGNAL("triggered()"), self.action_item_fix_history_rec_error)
        self.connect(self.ui.action_fix_file_not_found_try_find, 
                     QtCore.SIGNAL("triggered()"), self.action_fix_file_not_found_try_find)
        self.connect(self.ui.action_fix_file_not_found_delete, 
                     QtCore.SIGNAL("triggered()"), self.action_fix_file_not_found_delete)
        
        #MENU: Help
        self.connect(self.ui.action_help_about, 
                     QtCore.SIGNAL("triggered()"), self.action_help_about)
                        

    def create_items_table_context_menu(self):
        menu = QtGui.QMenu(self)
        menu.addAction(self.ui.action_item_view)
        menu.addAction(self.ui.action_item_view_m3u)
        menu.addAction(self.ui.action_item_view_image_viewer)
        menu.addAction(self.ui.action_item_to_external_filemanager)
        menu.addMenu(self.ui.menuExport_items)
        menu.addSeparator()
        menu.addAction(self.ui.action_item_edit)
        menu.addAction(self.ui.action_item_rebuild_thumbnail)        
        menu.addSeparator()
        menu.addAction(self.ui.action_item_delete)
        menu.addSeparator()
        menu.addAction(self.ui.action_item_check_integrity)
        menu.addMenu(self.ui.menuFix_integrity_errors)
        return menu
        

    def closeEvent(self, event):
        #Storing all dock widgets position and size
        byte_arr = self.saveState()
        UserConfig().store("main_window.state", str(byte_arr.data()))
        
        #Storing main window size
        UserConfig().storeAll({"main_window.width":self.width(), "main_window.height":self.height()})
        
        self.ui.dockWidget_items_table.save_columns_width()
        
        #Storing file browser table columns width
        self.save_file_browser_state()
        
        print("========= Reggata stopped at {} =========".format(datetime.datetime.now()))
        print()
        
    
    
    def restore_file_browser_state(self):
        self.ui.file_browser.setColumnWidth(FileBrowserTableModel.FILENAME, 
                                            int(UserConfig().get("file_browser.FILENAME.width", 450)))
        self.ui.file_browser.setColumnWidth(FileBrowserTableModel.TAGS, 
                                            int(UserConfig().get("file_browser.TAGS.width", 280)))
        self.ui.file_browser.setColumnWidth(FileBrowserTableModel.USERS, 
                                            int(UserConfig().get("file_browser.USERS.width", 100)))
        self.ui.file_browser.setColumnWidth(FileBrowserTableModel.STATUS, 
                                            int(UserConfig().get("file_browser.STATUS.width", 100)))
        self.ui.file_browser.setColumnWidth(FileBrowserTableModel.RATING, 
                                            int(UserConfig().get("file_browser.RATING.width", 100)))


    def save_file_browser_state(self):
        #Storing file browser table columns width
        width = self.ui.file_browser.columnWidth(FileBrowserTableModel.FILENAME)
        if width > 0:
            UserConfig().store("file_browser.FILENAME.width", str(width))
            
        width = self.ui.file_browser.columnWidth(FileBrowserTableModel.TAGS)
        if width > 0:
            UserConfig().store("file_browser.TAGS.width", str(width))
        
        width = self.ui.file_browser.columnWidth(FileBrowserTableModel.USERS)
        if width > 0:
            UserConfig().store("file_browser.USERS.width", str(width))
        
        width = self.ui.file_browser.columnWidth(FileBrowserTableModel.STATUS)
        if width > 0:
            UserConfig().store("file_browser.STATUS.width", str(width))
                                        
        width = self.ui.file_browser.columnWidth(FileBrowserTableModel.RATING)
        if width > 0:
            UserConfig().store("file_browser.RATING.width", str(width))
                    

    def event(self, e):
        return super(MainWindow, self).event(e)

    def reset_tag_cloud(self):
        self.ui.tag_cloud.reset()
    
    
        
    def query_reset(self):
        if self.model:
            self.model.query("")
        self.ui.dockWidget_items_table.query_text_reset()
        self.ui.tag_cloud.reset()
        
        
    def query_exec(self):
        try:
            if not self.active_repo:
                raise MsgException(self.tr("Open a repository first."))
            query_text = self.ui.dockWidget_items_table.query_text()
            limit = self.ui.dockWidget_items_table.query_limit()
            page = self.ui.dockWidget_items_table.query_page()
            self.model.query(query_text, limit, page)
            self.ui.dockWidget_items_table.resize_rows_to_contents()
            
        except Exception as ex:
            show_exc_info(self, ex)
        
        
    
    def _login_recent_user(self):
        if self.active_repo is None:
            raise MsgException(self.tr("You cannot login because there is no opened repo."))
        
        login = UserConfig().get("recent_user.login")
        password = UserConfig().get("recent_user.password")
        
        uow = self.active_repo.create_unit_of_work()
        try:
            self.active_user = uow.login_user(login, password)
        finally:
            uow.close()
        
            
    def _set_active_user(self, user):
        if type(user) != User and user is not None:
            raise TypeError(self.tr("Argument must be an instance of User class."))
        
        if self.__active_user is not None:
            self.ui.tag_cloud.remove_user(self.__active_user.login)            
        
        self.__active_user = user
        
        
        if user is not None:
            self.ui.tag_cloud.add_user(user.login)
        
            #Tell to table model that current active user has changed
            if self.model is not None and isinstance(self.model, RepoItemTableModel):
                self.model.user_login = user.login
        
            self.ui.label_user.setText("<b>" + user.login + "</b>")
            
            UserConfig().storeAll({"recent_user.login":user.login, "recent_user.password":user.password})
            
            self.ui.file_browser.model().user_login = user.login
        else:
            self.ui.label_user.setText("")
            self.ui.file_browser.model().user_login = None
        
        
    def _get_active_user(self):
        return self.__active_user
    
    active_user = property(_get_active_user, 
                           _set_active_user, 
                           doc="Active user is a user after sucessfull login.")
    
    
    def _set_active_repo(self, repo):
        if not isinstance(repo, RepoMgr) and not repo is None:
            raise TypeError(self.tr("Argument must be of RepoMgr class."))
    
        try:
            self.__active_repo = repo
            
            self.ui.tag_cloud.repo = repo
            
            if repo is not None:
                UserConfig().store("recent_repo.base_path", repo.base_path)
                    
                (head, tail) = os.path.split(repo.base_path)
                while tail == "" and head != "":
                    (head, tail) = os.path.split(head)
                self.ui.label_repo.setText("<b>" + tail + "</b>")
                
                self.ui.statusbar.showMessage(self.tr("Opened repository from {}.")
                                              .format(repo.base_path), 5000)
                
                self.model = RepoItemTableModel(
                    repo, self.items_lock, 
                    self.active_user.login if self.active_user is not None else None)
                self.ui.dockWidget_items_table.setTableModel(self.model)                
                
                self.ui.file_browser.repo = repo         
                 
                completer = helpers.Completer(repo=repo, parent=self.ui.dockWidget_items_table)
                self.ui.dockWidget_items_table.set_tag_completer(completer)
                
                self.restore_file_browser_state()
                self.ui.dockWidget_items_table.restore_columns_width()
                
            else:
                self.save_file_browser_state()
                self.ui.dockWidget_items_table.save_columns_width()
                
                self.ui.label_repo.setText("")
                self.model = None
                self.ui.dockWidget_items_table.setTableModel(None)
                self.ui.file_browser.repo = None
            
                self.ui.dockWidget_items_table.set_tag_completer(None)
                
                
                
        except Exception as ex:
            raise CannotOpenRepoError(str(ex), ex)
                
    def _get_active_repo(self):
        return self.__active_repo
    
    active_repo = property(_get_active_repo, 
                           _set_active_repo, 
                           doc="Repo that has been opened.")
        
        
    def action_repo_create(self):
        try:
            base_path = QtGui.QFileDialog.getExistingDirectory(
                self, self.tr("Choose a base path for new repository"))
            if not base_path:
                raise MsgException(self.tr("You haven't chosen existent directory. Operation canceled."))
            
            #QFileDialog returns forward slashed in windows! Because of this path should be normalized
            base_path = os.path.normpath(base_path)
            self.active_repo = RepoMgr.create_new_repo(base_path)
            self.active_user = None
        except Exception as ex:
            show_exc_info(self, ex)
        else:        
            #Let user create a user account in new repository    
            self.action_user_create()
        
        
    def action_repo_close(self):
        try:
            if self.active_repo is None:
                raise MsgException(self.tr("There is no opened repository."))
            self.active_repo = None
            self.active_user = None
        except Exception as ex:
            show_exc_info(self, ex)
                    

    def action_repo_open(self):
        try:            
            base_path = QtGui.QFileDialog.getExistingDirectory(self, self.tr("Choose a repository base path"))
            
            if not base_path:
                raise Exception(self.tr("You haven't chosen existent directory. Operation canceled."))

            #QFileDialog returns forward slashed in windows! Because of this path should be normalized
            base_path = os.path.normpath(base_path)
            self.active_repo = RepoMgr(base_path)
            self.active_user = None
            self._login_recent_user()
            
            
        
        except LoginError:
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
            
            rows = self.ui.dockWidget_items_table.selected_rows()
            if len(rows) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            mb = QtGui.QMessageBox()
            mb.setText(self.tr("Do you really want to delete {} selected file(s)?").format(len(rows)))
            mb.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            if mb.exec_() == QtGui.QMessageBox.Yes:
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
            sel_rows = self.ui.dockWidget_items_table.selected_rows()
            if len(sel_rows) != 1:
                raise MsgException(self.tr("Select one item, please."))
            
            sel_row = sel_rows.pop()
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
            
            rows = self.ui.dockWidget_items_table.selected_rows()
            if len(rows) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            start_index = 0
            abs_paths = []
            if len(rows) == 1:
                #If there is only one selected item, pass to viewer all items in this table model
                for row in range(self.model.rowCount()):
                    abs_paths.append(os.path.join(self.active_repo.base_path, self.model.items[row].data_ref.url))
                #This is the index of the first image to show
                start_index = rows.pop()
            else:
                for row in rows:
                    abs_paths.append(os.path.join(self.active_repo.base_path, self.model.items[row].data_ref.url))
            
            iv = ImageViewer(self.active_repo, self.active_user.login, self, abs_paths)
            iv.set_current_image_index(start_index)
            iv.show()
            
            #TODO scroll items table to the last item shown in ImageViewer 
            
            
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
            
            rows = self.ui.dockWidget_items_table.selected_rows()
            if len(rows) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            items = []
            for row in rows:
                self.model.items[row].table_row = row
                items.append(self.model.items[row])
                        
            thread = ItemIntegrityFixerThread(self, self.active_repo, items, self.items_lock, strategy, self.active_user.login)
            
            self.connect(thread, QtCore.SIGNAL("exception"), 
                         lambda exc_info: show_exc_info(self, exc_info[1], details=format_exc_info(*exc_info)))
            self.connect(thread, QtCore.SIGNAL("finished"), 
                         lambda: self.ui.statusbar.showMessage(self.tr("Integrity fixing is done.")))
            self.connect(thread, QtCore.SIGNAL("progress"), 
                         lambda percents, row: refresh(percents, row))
            thread.start()
            
        except Exception as ex:
            show_exc_info(self, ex)
        else:
            pass


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
            
            rows = self.ui.dockWidget_items_table.selected_rows()
            if len(rows) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            items = []
            for row in rows:
                self.model.items[row].table_row = row
                items.append(self.model.items[row])
             
            thread = ItemIntegrityCheckerThread(self, self.active_repo, items, self.items_lock)
            self.connect(thread, QtCore.SIGNAL("exception"), 
                         lambda msg: raise_exc(msg))
            self.connect(thread, QtCore.SIGNAL("finished"), 
                         lambda error_count: self.ui.statusbar.showMessage(self.tr("Integrity check is done. {0} Items with errors.").format(error_count)))            
            self.connect(thread, QtCore.SIGNAL("progress"), 
                         lambda percents, row: refresh(percents, row))
            thread.start()
            
        except Exception as ex:
            show_exc_info(self, ex)
        else:
            pass


    def action_export_selected_items(self):
        try:
            if self.active_repo is None:
                raise MsgException(self.tr("Open a repository first."))
            
            item_ids = self.ui.dockWidget_items_table.selected_item_ids()
            if len(item_ids) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            export_dir_path = QtGui.QFileDialog.getExistingDirectory(
                self, self.tr("Choose a directory path to export files into."))
            if not export_dir_path:
                raise MsgException(self.tr("You haven't chosen existent directory. Operation canceled."))
            
            thread = ExportItemsThread(self, self.active_repo, item_ids, export_dir_path)
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

    def action_export_items_file_paths(self):
        try:
            if self.active_repo is None:
                raise MsgException(self.tr("Open a repository first."))
            
            rows = self.ui.dockWidget_items_table.selected_rows()
            if len(rows) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            export_filename = QtGui.QFileDialog.getSaveFileName(parent=self, caption=self.tr('Save results in a file.')) 
            if not export_filename:
                raise MsgException(self.tr("Operation canceled."))
            
            file = open(export_filename, "w", newline='')
            for row in rows:
                item = self.model.items[row]
                if item.is_data_ref_null():
                    continue
                textline = self.active_repo.base_path + \
                    os.sep + self.model.items[row].data_ref.url + os.linesep
                file.write(textline)
            file.close()

        except Exception as ex:
            show_exc_info(self, ex)
        else:
            self.ui.statusbar.showMessage(self.tr("Operation completed."), 5000)

    def action_item_view_m3u(self):
        try:
            if self.active_repo is None:
                raise MsgException(self.tr("Open a repository first."))
            
            if self.active_user is None:
                raise MsgException(self.tr("Login to a repository first."))
            
            rows = self.ui.dockWidget_items_table.selected_rows()
            if len(rows) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            tmp_dir = UserConfig().get("tmp_dir", consts.DEFAULT_TMP_DIR)
            if not os.path.exists(tmp_dir):
                os.makedirs(tmp_dir)
            m3u_filename = str(os.getpid()) + self.active_user.login + str(time.time()) + ".m3u"
            m3u_file = open(os.path.join(tmp_dir, m3u_filename), "wt")
            for row in rows:
                m3u_file.write(os.path.join(self.active_repo.base_path, 
                                            self.model.items[row].data_ref.url) + os.linesep)                                            
            m3u_file.close()
            
            eam = ExtAppMgr()
            eam.invoke(os.path.join(tmp_dir, m3u_filename))
            
        except Exception as ex:
            show_exc_info(self, ex)
        else:
            self.ui.statusbar.showMessage(self.tr("Operation completed."), 5000)


    def action_item_add_many_rec(self):
        ''' Add many items recursively from given directory to the repo.
        '''
        thread = None
        try:
            if self.active_repo is None:
                raise MsgException(self.tr("Open a repository first."))
            
            if self.active_user is None:
                raise MsgException(self.tr("Login to a repository first."))
            
            
            dir = QtGui.QFileDialog.getExistingDirectory(self, self.tr("Select one directory"))
            if not dir:
                raise MsgException(self.tr("Directory is not chosen. Operation cancelled."))
                        
            dir = os.path.normpath(dir)
            
            items = []
            for root, dirs, files in os.walk(dir):
                for file in files:
                    absPathToFile = os.path.join(root, file)
                    item = Item(user_login=self.active_user.login)
                    item.title = file
                    item.data_ref = DataRef(type=DataRef.FILE, url=None) #DataRef.url doesn't important here
                    item.data_ref.srcAbsPath = absPathToFile
                    item.data_ref.srcAbsPathToRecursionRoot = dir
                    items.append(item)
            
            completer = helpers.Completer(self.active_repo, self)
            d = ItemsDialog(self, items, ItemsDialog.CREATE_MODE, same_dst_path=False, completer=completer)
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
        finally:
            self.ui.statusbar.showMessage(self.tr("Operation completed. Stored {} files, skipped {} files.").format(thread.created_objects_count, len(thread.error_log)))
            self.query_exec()
            self.ui.tag_cloud.refresh()
            
            
        
    def action_item_add_many(self):
        '''Add many Items to the repo.'''
        thread = None
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
                file = os.path.normpath(file)
                item = Item(user_login=self.active_user.login)
                item.title = os.path.basename(file)
                item.data_ref = DataRef(type=DataRef.FILE, url=None) #DataRef.url doesn't important here
                item.data_ref.srcAbsPath = file
                items.append(item)
            
            completer = helpers.Completer(self.active_repo, self)
            d = ItemsDialog(self, items, ItemsDialog.CREATE_MODE, completer=completer)
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
        finally:
            self.ui.statusbar.showMessage(self.tr("Operation completed. Stored {} files, skipped {} files.").format(thread.created_objects_count, len(thread.error_log)))
            self.query_exec()
            self.ui.tag_cloud.refresh()
        
        
    def action_item_add(self):
        '''Add single Item to the repo.'''
        try:
            if self.active_repo is None:
                raise MsgException(self.tr("Open a repository first."))
            
            if self.active_user is None:
                raise MsgException(self.tr("Login to a repository first."))
            
            item = Item(user_login=self.active_user.login)
            
            #User can push Cancel button and do not select a file now
            file = QtGui.QFileDialog.getOpenFileName(self, self.tr("Select a file to link with new Item."))
            if not is_none_or_empty(file):
                file = os.path.normpath(file)
                item.title = os.path.basename(file)
                item.data_ref = DataRef(type=DataRef.FILE, url=file)
            
            
            completer = helpers.Completer(self.active_repo, self)
            dialog = ItemDialog(self, item, ItemDialog.CREATE_MODE, completer=completer)
            if dialog.exec_():
                uow = self.active_repo.create_unit_of_work()
                try:
                    srcAbsPath = None
                    dstRelPath = None
                    if dialog.item.data_ref is not None:
                        srcAbsPath = dialog.item.data_ref.srcAbsPath
                        dstRelPath = dialog.item.data_ref.dstRelPath

                    thread = BackgrThread(self, uow.saveNewItem, dialog.item, srcAbsPath, dstRelPath)
                    
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
            self.ui.tag_cloud.refresh()
    
    def action_user_create(self):
        try:
            if self.active_repo is None:
                raise Exception(self.tr("Open a repository first."))
            
            u = UserDialog(User(), self)
            if u.exec_():
                uow = self.active_repo.create_unit_of_work()
                try:
                    uow.save_new_user(u.user)
                    
                    self.active_user = u.user                    
                finally:
                    uow.close()
        except Exception as ex:
            show_exc_info(self, ex)
        

    def action_user_change_pass(self):
        try:
            #TODO should be implemented...
            raise NotImplementedError("This function is not implemented yet.")
        except Exception as ex:
            show_exc_info(self, ex)
        else:
            self.ui.statusbar.showMessage(self.tr("Operation completed."), 5000)
        
        

    def action_user_login(self):
        try:
            if self.active_repo is None:
                raise MsgException(self.tr("There is no opened repository."))
            
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
            
            rows = self.ui.dockWidget_items_table.selected_rows()
            if len(rows) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            
            uow = self.active_repo.create_unit_of_work()
            try:
                items = []
                for row in rows:                    
                    self.model.items[row].table_row = row
                    items.append(self.model.items[row])
                 
                thread = ThumbnailBuilderThread(self, self.active_repo, items, self.items_lock, rebuild=True)
                self.connect(thread, QtCore.SIGNAL("exception"), 
                             lambda exc_info: helpers.show_exc_info(self, exc_info[1], details=format_exc_info(*exc_info)))
                self.connect(thread, QtCore.SIGNAL("finished"), 
                             lambda: self.ui.statusbar.showMessage(self.tr("Rebuild thumbnails is done.")))            
                self.connect(thread, QtCore.SIGNAL("progress"), 
                             lambda percents, row: refresh(percents, row))
                thread.start()
                    
            finally:
                uow.close()
                    
                                
            
        except Exception as ex:
            show_exc_info(self, ex)
        else:
            pass
            

    def action_item_to_external_filemanager(self):
        try:
            sel_rows = self.ui.dockWidget_items_table.selected_rows()
            if len(sel_rows) != 1:
                raise MsgException(self.tr("Select one item, please."))
            
            sel_row = sel_rows.pop()
            data_ref = self.model.items[sel_row].data_ref
            
            if not data_ref or data_ref.type != DataRef.FILE:
                raise MsgException(
                self.tr("Action '%1' can be applied only to items linked with files.")
                .arg(self.ui.action_item_to_external_filemanager.text()))
            
            eam = ExtAppMgr()
            eam.external_file_manager(os.path.join(self.active_repo.base_path, data_ref.url))
                        
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
            
            rows = self.ui.dockWidget_items_table.selected_rows()
            if len(rows) == 0:
                raise MsgException(self.tr("There are no selected items."))
            
            if len(rows) > 1:                
                uow = self.active_repo.create_unit_of_work()
                try:
                    sel_items = []
                    for row in rows:
                        id = self.model.items[row].id
                        sel_items.append(uow.getExpungedItem(id))
                    completer = helpers.Completer(self.active_repo, self)
                    dlg = ItemsDialog(self, sel_items, ItemsDialog.EDIT_MODE, completer=completer)
                    if dlg.exec_():
                        thread = UpdateGroupOfItemsThread(self, self.active_repo, sel_items)
                        self.connect(thread, QtCore.SIGNAL("exception"), 
                                     lambda msg: raise_exc(msg))
                                                                        
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
                item_id = self.model.items[rows.pop()].id
                uow = self.active_repo.create_unit_of_work()
                try:
                    item = uow.getExpungedItem(item_id)
                    completer = helpers.Completer(self.active_repo, self)
                    item_dialog = ItemDialog(self, item, ItemDialog.EDIT_MODE, completer=completer)
                    if item_dialog.exec_():
                        uow.updateExistingItem(item_dialog.item, self.active_user.login)
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
            


class AboutDialog(QtGui.QDialog):
    
    def __init__(self, parent=None):
        super(AboutDialog, self).__init__(parent)
        self.ui = ui_aboutdialog.Ui_AboutDialog()
        self.ui.setupUi(self)
        
        title = '''<h1>Reggata</h1>'''
        text = \
'''
<p>Reggata is a tagging system for local files.
</p>

<p>Copyright 2010 Vitaly Volkov, <font color="blue">vitvlkv@gmail.com</font>
</p>

<p>Home page: <font color="blue">http://github.com/vlkv/reggata</font>
</p>

<p>Reggata is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
</p>

<p>Reggata is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
</p>

<p>You should have received a copy of the GNU General Public License
along with Reggata.  If not, see <font color="blue">http://www.gnu.org/licenses</font>.
</p>
'''
        f = None
        try:
            #print(os.path.abspath(os.curdir))
            #print(__file__)
            try:
                f = open(os.path.join(os.path.dirname(__file__), "version.txt", "r"))
            except:
                try:
                    f = open(os.path.join(os.path.dirname(__file__), os.pardir, "version.txt"), "r")
                except:
                    f = open(os.path.join(os.path.abspath(os.curdir), "version.txt"), "r")
            version = f.readline()
            text = "<p>Version: " + version + "</p>" + text
        except Exception as ex:
            text = "<p>Version: " + "<font color='red'>&lt;no information&gt;</font>" + "</p>" + text
        finally:
            if f:
                f.close()
                        
        self.ui.textEdit.setHtml(title + text)
