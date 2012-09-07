'''
Created on 21.01.2012

@author: vlkv
'''
import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui
from PyQt4.QtCore import Qt

import ui_itemstabledockwidget
from user_config import UserConfig
from gui.table_models import RepoItemTableModel
from parsers import query_parser
from gui.common_widgets import TextEdit
from helpers import *
import consts
import logging
from errors import *

logger = logging.getLogger(consts.ROOT_LOGGER + "." + __name__)

class ItemsTableDockWidget(QtGui.QDockWidget):
    
    def __init__(self, parent):
        super(ItemsTableDockWidget, self).__init__(parent)
        self.ui = ui_itemstabledockwidget.Ui_ItemsTableDockWidget()
        self.ui.setupUi(self)
        
        self.itemsTableModel = None
        
        #Widgets for text queries
        self.ui.lineEdit_query = TextEdit(self, one_line=True)
        tmp = QtGui.QHBoxLayout(self.ui.widget_lineEdit_query)
        tmp.addWidget(self.ui.lineEdit_query)        
        self.connect(self.ui.pushButton_query_exec, QtCore.SIGNAL("clicked()"), self.query_exec)
        self.connect(self.ui.lineEdit_query, QtCore.SIGNAL("returnPressed()"), self.ui.pushButton_query_exec.click)
        self.connect(self.ui.pushButton_query_reset, QtCore.SIGNAL("clicked()"), self.query_reset)
        
        #TODO limit page function sometimes works not correct!!! It sometimes shows less items, than specified in limit spinbox!
        #Initialization of limit and page spinboxes 
        self.ui.spinBox_limit.setValue(int(UserConfig().get("spinBox_limit.value", 0)))
        self.ui.spinBox_limit.setSingleStep(int(UserConfig().get("spinBox_limit.step", 5)))
        self.connect(self.ui.spinBox_limit, QtCore.SIGNAL("valueChanged(int)"), self.query_exec)
        self.connect(self.ui.spinBox_limit, QtCore.SIGNAL("valueChanged(int)"), lambda: UserConfig().store("spinBox_limit.value", self.ui.spinBox_limit.value()))
        self.connect(self.ui.spinBox_limit, QtCore.SIGNAL("valueChanged(int)"), lambda val: self.ui.spinBox_page.setEnabled(val > 0))
        self.connect(self.ui.spinBox_page, QtCore.SIGNAL("valueChanged(int)"), self.query_exec)
        self.ui.spinBox_page.setEnabled(self.ui.spinBox_limit.value() > 0)
        
        #Tuning table cell rendering
        self.ui.tableView_items.setItemDelegateForColumn(RepoItemTableModel.TITLE, HTMLDelegate(self))
        self.ui.tableView_items.setItemDelegateForColumn(RepoItemTableModel.IMAGE_THUMB, ImageThumbDelegate(self))                 
        self.ui.tableView_items.setItemDelegateForColumn(RepoItemTableModel.RATING, RatingDelegate(self))
        
        #Turn on table sorting
        self.ui.tableView_items.setSortingEnabled(True)
        
        self.__table_model = None
        self.__context_menu = None
    
    def query_exec(self):
        try:
            if self.__table_model is None:
                raise MsgException(self.tr("Items Table Widget has no Model."))
            
            query_text = self.query_text()
            limit = self.query_limit()
            page = self.query_page()
            
            self.__table_model.query(query_text, limit, page)
        
            self.resize_rows_to_contents()
            
        except Exception as ex:
            logger.warning(str(ex))
            show_exc_info(self, ex)
    
    
    def query_reset(self):
        if self.__table_model is not None:
            self.__table_model.query("")
        self.query_text_reset()
        self.emit(QtCore.SIGNAL("queryTextResetted"))
    

    def query_text(self):
        return self.ui.lineEdit_query.text()
    
    def query_text_reset(self):
        self.ui.lineEdit_query.setText("")
    
    def set_tag_completer(self, completer):
        self.ui.lineEdit_query.set_completer(completer)
    
    def query_limit(self):
        return self.ui.spinBox_limit.value()
    
    def query_page(self):
        return self.ui.spinBox_page.value()
    
    def selected_rows(self):
        #We use set, because selectedIndexes() may return duplicates
        rows = set()
        for index in self.ui.tableView_items.selectionModel().selectedIndexes():
            rows.add(index.row())
        return rows

    def selected_item_ids(self):
        #We use set, because selectedIndexes() may return duplicates
        item_ids = set()
        for index in self.ui.tableView_items.selectionModel().selectedIndexes():
            item_ids.add(self.__table_model.items[index.row()].id)
        return item_ids
        

    def selected_tags_changed(self, tags, not_tags):
        #TODO Нужно заключать в кавычки имена тегов, содержащие недопустимые символы
        text = ""
        for tag in tags:
            text = text + tag + " "
        for tag in not_tags:
            text = text + query_parser.NOT_OPERATOR + " " + tag + " "
        text = self.ui.lineEdit_query.setText(text)
        self.query_exec()
    
    def addContextMenu(self, menu):
        self.__context_menu = menu
        self.ui.tableView_items.setContextMenuPolicy(Qt.CustomContextMenu)
        self.connect(self.ui.tableView_items, QtCore.SIGNAL("customContextMenuRequested(const QPoint &)"), self.showContextMenu)
    
    def showContextMenu(self, pos):
        self.__context_menu.exec_(self.ui.tableView_items.mapToGlobal(pos))
        
    def setTableModel(self, model):
        self.__table_model = model
        self.ui.tableView_items.setModel(model)
        if model is not None:
            self.connect(model, QtCore.SIGNAL("modelReset()"), self.ui.tableView_items.resizeRowsToContents)
            self.connect(model, QtCore.SIGNAL("dataChanged(const QModelIndex&, const QModelIndex&)"), self._resize_row_to_contents)
        
    def _resize_row_to_contents(self, top_left, bottom_right):
        if top_left.row() == bottom_right.row():
            self.ui.tableView_items.resizeRowToContents(top_left.row())
            
        elif top_left.row() < bottom_right.row():
            for row in range(top_left.row(), bottom_right.row()):
                self.ui.tableView_items.resizeRowToContents(row)
                
    def resize_rows_to_contents(self):
        self.ui.tableView_items.resizeRowsToContents()

    def restore_columns_width(self):
        self.ui.tableView_items.setColumnWidth(RepoItemTableModel.ID, int(UserConfig().get("items_table.ID.width", 55)))
        self.ui.tableView_items.setColumnWidth(RepoItemTableModel.TITLE, int(UserConfig().get("items_table.TITLE.width", 430)))
        self.ui.tableView_items.setColumnWidth(RepoItemTableModel.IMAGE_THUMB, int(UserConfig().get("thumbnail_size", consts.THUMBNAIL_DEFAULT_SIZE)))
        self.ui.tableView_items.setColumnWidth(RepoItemTableModel.LIST_OF_TAGS, int(UserConfig().get("items_table.LIST_OF_TAGS.width", 220)))
        self.ui.tableView_items.setColumnWidth(RepoItemTableModel.STATE, int(UserConfig().get("items_table.STATE.width", 100)))
        self.ui.tableView_items.setColumnWidth(RepoItemTableModel.RATING, int(UserConfig().get("items_table.RATING.width", 100)))
        
    def save_columns_width(self):
        width_id = self.ui.tableView_items.columnWidth(RepoItemTableModel.ID)
        if width_id > 0:            
            UserConfig().store("items_table.ID.width", str(width_id))
                        
        width_title = self.ui.tableView_items.columnWidth(RepoItemTableModel.TITLE)
        if width_title > 0:
            UserConfig().store("items_table.TITLE.width", str(width_title))
        
        width_list_of_tags = self.ui.tableView_items.columnWidth(RepoItemTableModel.LIST_OF_TAGS)
        if width_list_of_tags > 0:
            UserConfig().store("items_table.LIST_OF_TAGS.width", str(width_list_of_tags))
        
        width_state = self.ui.tableView_items.columnWidth(RepoItemTableModel.STATE)
        if width_state > 0:
            UserConfig().store("items_table.STATE.width", str(width_state))
        
        width_rating = self.ui.tableView_items.columnWidth(RepoItemTableModel.RATING)
        if width_rating > 0:
            UserConfig().store("items_table.RATING.width", str(width_rating))
    
    