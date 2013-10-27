'''
Created on 21.01.2012
@author: vlkv
'''
import logging
import os
import traceback
import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui
from PyQt4.QtCore import Qt
import reggata.helpers as helpers
import reggata.consts as consts
import reggata.errors as errors
import reggata.data.commands as cmds
import reggata.statistics as stats
import reggata.data.db_schema as db
from reggata.gui.common_widgets import TextEdit
from reggata.logic.worker_threads import ThumbnailBuilderThread
from reggata.gui.tool_gui import ToolGui
from reggata.ui.ui_itemstablegui import Ui_ItemsTableGui
from reggata.user_config import UserConfig
from reggata.parsers import query_parser, query_tokens
from reggata.gui.univ_table_model import UnivTableModel, UnivTableView




logger = logging.getLogger(__name__)


class ItemsTableGui(ToolGui):

    def __init__(self, parent, itemsTableTool):
        super(ItemsTableGui, self).__init__(parent)
        self.ui = Ui_ItemsTableGui()
        self.ui.setupUi(self)

        self.ui.tableView_items = UnivTableView(self)
        self.ui.tableViewContainer.addWidget(self.ui.tableView_items)

        self.__itemsTableTool = itemsTableTool

        #Widgets for text queries
        self.ui.lineEdit_query = TextEdit(self, one_line=True)
        tmp = QtGui.QHBoxLayout(self.ui.widget_lineEdit_query)
        tmp.addWidget(self.ui.lineEdit_query)
        self.connect(self.ui.pushButton_query_exec, QtCore.SIGNAL("clicked()"), self.query_exec)
        self.connect(self.ui.lineEdit_query, QtCore.SIGNAL("returnPressed()"), self.ui.pushButton_query_exec.click)
        self.connect(self.ui.pushButton_query_reset, QtCore.SIGNAL("clicked()"), self.query_reset)
        self.connect(self.ui.tableView_items, QtCore.SIGNAL("doubleClicked(const QModelIndex&)"), self.__onTableDoubleClicked)

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
#        self.ui.tableView_items.setItemDelegateForColumn(ItemsTableModel.TITLE, helpers.HTMLDelegate(self))
#        self.ui.tableView_items.setItemDelegateForColumn(ItemsTableModel.IMAGE_THUMB, helpers.ImageThumbDelegate(self))
#        self.ui.tableView_items.setItemDelegateForColumn(ItemsTableModel.RATING, helpers.RatingDelegate(self))

        #Turn on table sorting
        self.ui.tableView_items.setSortingEnabled(True)

        self.__table_model = None

        self.__context_menu = None
        self.__initContextMenu()


    def __getTableModel(self):
        return self.__table_model

    def __setTableModel(self, model):
        self.__table_model = model
        self.ui.tableView_items.setModel(model)
        if model is not None:
            self.connect(model, QtCore.SIGNAL("modelReset()"), self.ui.tableView_items.resizeRowsToContents)
            self.connect(model, QtCore.SIGNAL("dataChanged(const QModelIndex&, const QModelIndex&)"), self._resize_row_to_contents)

    itemsTableModel = property(fget=__getTableModel, fset=__setTableModel)


    def update(self):
        self.query_exec()


    def query_exec(self):
        try:
            if self.__table_model is None:
                raise errors.MsgException(self.tr("Items Table Widget has no Model."))

            query_text = self.query_text()
            limit = self.query_limit()
            page = self.query_page()

            self.__table_model.query(query_text, limit, page)

            self.resize_rows_to_contents()

            stats.sendEvent("items_table.query_exec")


        except Exception as ex:
            logger.warning(str(ex))
            helpers.show_exc_info(self, ex)


    def query_reset(self):
        if self.__table_model is not None:
            self.__table_model.query("")
        self.query_text_reset()
        self.emit(QtCore.SIGNAL("queryTextResetted"))
        stats.sendEvent("items_table.query_reset")


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

    def selectedRows(self):
        #We use set, because selectedIndexes() may return duplicates
        rows = set()
        for index in self.ui.tableView_items.selectionModel().selectedIndexes():
            rows.add(index.row())
        return rows

    def selectedItemIds(self):
        #We use set, because selectedIndexes() may return duplicates
        item_ids = set()
        for index in self.ui.tableView_items.selectionModel().selectedIndexes():
            item_ids.add(self.__table_model.objAtRow(index.row()).id)
        return item_ids


    def itemAtRow(self, row):
        return self.__table_model.objAtRow(row)


    def rowCount(self):
        return self.__table_model.rowCount()


    def resetSingleRow(self, row):
        self.__table_model.resetRowRange(row, row)

    def resetRowRange(self, topRow, bottomRow):
        self.__table_model.resetRowRange(topRow, bottomRow)


    def selectedKeywordAll(self):
        self.ui.lineEdit_query.setText("ALL")
        self.query_exec()


    def selected_tags_changed(self, tags, not_tags):
        text = ""
        for tag in tags:
            text = text + tag + " "
        for tag in not_tags:
            text = text + query_tokens.NOT_OPERATOR + " " + tag + " "
        self.ui.lineEdit_query.setText(text)
        self.query_exec()


    def _resize_row_to_contents(self, top_left, bottom_right):
        if top_left.row() == bottom_right.row():
            self.ui.tableView_items.resizeRowToContents(top_left.row())

        elif top_left.row() < bottom_right.row():
            for row in range(top_left.row(), bottom_right.row()):
                self.ui.tableView_items.resizeRowToContents(row)

    def resize_rows_to_contents(self):
        self.ui.tableView_items.resizeRowsToContents()


    def restore_columns_width(self):
#        self.ui.tableView_items.setColumnWidth(ItemsTableModel.ROW_NUMBER, int(UserConfig().get("items_table.ROW_NUMBER.width", 30)))
#        self.ui.tableView_items.setColumnWidth(ItemsTableModel.ID, int(UserConfig().get("items_table.ID.width", 55)))
#        self.ui.tableView_items.setColumnWidth(ItemsTableModel.TITLE, int(UserConfig().get("items_table.TITLE.width", 430)))
#        self.ui.tableView_items.setColumnWidth(ItemsTableModel.IMAGE_THUMB, int(UserConfig().get("thumbnail_size", consts.THUMBNAIL_DEFAULT_SIZE)))
#        self.ui.tableView_items.setColumnWidth(ItemsTableModel.LIST_OF_TAGS, int(UserConfig().get("items_table.LIST_OF_TAGS.width", 220)))
#        self.ui.tableView_items.setColumnWidth(ItemsTableModel.STATE, int(UserConfig().get("items_table.STATE.width", 100)))
#        self.ui.tableView_items.setColumnWidth(ItemsTableModel.RATING, int(UserConfig().get("items_table.RATING.width", 100)))
        pass

    def save_columns_width(self):
#        widthRowNumber = self.ui.tableView_items.columnWidth(ItemsTableModel.ROW_NUMBER)
#        if widthRowNumber > 0:
#            UserConfig().store("items_table.ROW_NUMBER.width", str(widthRowNumber))
#
#        width_id = self.ui.tableView_items.columnWidth(ItemsTableModel.ID)
#        if width_id > 0:
#            UserConfig().store("items_table.ID.width", str(width_id))
#
#        width_title = self.ui.tableView_items.columnWidth(ItemsTableModel.TITLE)
#        if width_title > 0:
#            UserConfig().store("items_table.TITLE.width", str(width_title))
#
#        width_list_of_tags = self.ui.tableView_items.columnWidth(ItemsTableModel.LIST_OF_TAGS)
#        if width_list_of_tags > 0:
#            UserConfig().store("items_table.LIST_OF_TAGS.width", str(width_list_of_tags))
#
#        width_state = self.ui.tableView_items.columnWidth(ItemsTableModel.STATE)
#        if width_state > 0:
#            UserConfig().store("items_table.STATE.width", str(width_state))
#
#        width_rating = self.ui.tableView_items.columnWidth(ItemsTableModel.RATING)
#        if width_rating > 0:
#            UserConfig().store("items_table.RATING.width", str(width_rating))
        pass

    def buildActions(self):
        if len(self.actions) > 0:
            logger.info("Actions already built")
            return

        self.actions['addItems'] = self._createAction(self.tr("Add items"))

        self.actions['editItem'] = self._createAction(self.tr("Edit item"))
        self.actions['rebuildItemsThumbnail'] = self._createAction(self.tr("Rebuild item's thumbnail"))

        self.actions['deleteItem'] = self._createAction(self.tr("Delete item"))

        self.actions['openItem'] = self._createAction(self.tr("Open item"))
        self.actions['openItemWithBuiltinImageViewer'] = self._createAction(self.tr("Open item with built-in Image Viewer"))
        self.actions['createM3uAndOpenIt'] = self._createAction(self.tr("Create m3u playlist and open it"))
        self.actions['openItemWithExternalFileManager'] = self._createAction(self.tr("Open containing directory"))

        self.actions['exportItems'] = self._createAction(self.tr("Export items"))
        self.actions['exportItemsFiles'] = self._createAction(self.tr("Export items' files"))
        self.actions['exportItemsFilePaths'] = self._createAction(self.tr("Export items' file paths"))

        self.actions['checkItemsIntegrity'] = self._createAction(self.tr("Check Item integrity"))
        self.actions['fixFileNotFoundTryFind'] = self._createAction(self.tr("Try find file"))
        self.actions['fixFileNotFoundRemoveDataRef'] = self._createAction(self.tr("Remove Item's reference to file"))
        self.actions['fixHashMismatchTryFind'] = self._createAction(self.tr("Try find file"))
        self.actions['fixHashMismatchUpdateHash'] = self._createAction(self.tr("Update file hash"))


    def buildMainMenu(self):
        assert len(self.actions) > 0, "Actions should be already built"
        if self._mainMenu is not None:
            logger.info("Main Menu of this Tool already built")
            return

        self._mainMenu = self._createMenu(self.tr("Items Table"), self)
        menu = self._mainMenu

        menu.addAction(self.actions['addItems'])
        menu.addSeparator()
        menu.addAction(self.actions['editItem'])
        menu.addAction(self.actions['rebuildItemsThumbnail'])
        menu.addSeparator()
        menu.addAction(self.actions['deleteItem'])
        menu.addSeparator()
        menu.addAction(self.actions['openItem'])
        menu.addAction(self.actions['openItemWithBuiltinImageViewer'])
        menu.addAction(self.actions['createM3uAndOpenIt'])
        menu.addAction(self.actions['openItemWithExternalFileManager'])
        menu.addSeparator()
        subMenuExport = self._createAndAddSubMenu(self.tr("Export"), self, menu)
        subMenuExport.addAction(self.actions['exportItems'])
        subMenuExport.addAction(self.actions['exportItemsFiles'])
        subMenuExport.addAction(self.actions['exportItemsFilePaths'])
        menu.addSeparator()
        menu.addAction(self.actions['checkItemsIntegrity'])
        subMenuFixFileNotFoundError = self._createAndAddSubMenu(self.tr("Fix File Not Found Error"), self, menu)
        subMenuFixFileNotFoundError.addAction(self.actions['fixFileNotFoundTryFind'])
        subMenuFixFileNotFoundError.addAction(self.actions['fixFileNotFoundRemoveDataRef'])
        subMenuFixHashMismatchError = self._createAndAddSubMenu(self.tr("Fix File Hash Mismatch Error"), self, menu)
        subMenuFixHashMismatchError.addAction(self.actions['fixHashMismatchTryFind'])
        subMenuFixHashMismatchError.addAction(self.actions['fixHashMismatchUpdateHash'])


    def __buildContextMenu(self):
        if self.__context_menu is not None:
            logger.info("Context menu of this Tool already built")
            return

        self.__context_menu = self._createMenu(menuTitle=None, menuParent=self)
        menu = self.__context_menu

        menu.addAction(self.actions['openItem'])
        menu.addAction(self.actions['openItemWithBuiltinImageViewer'])
        menu.addAction(self.actions['createM3uAndOpenIt'])
        menu.addAction(self.actions['openItemWithExternalFileManager'])
        menu.addSeparator()
        menu.addAction(self.actions['editItem'])
        menu.addAction(self.actions['rebuildItemsThumbnail'])
        menu.addSeparator()
        menu.addAction(self.actions['deleteItem'])
        menu.addSeparator()
        subMenuExport = self._createAndAddSubMenu(self.tr("Export"), self, menu)
        subMenuExport.addAction(self.actions['exportItems'])
        subMenuExport.addAction(self.actions['exportItemsFiles'])
        subMenuExport.addAction(self.actions['exportItemsFilePaths'])
        menu.addSeparator()
        menu.addAction(self.actions['checkItemsIntegrity'])
        subMenuFixFileNotFoundError = self._createAndAddSubMenu(self.tr("Fix File Not Found Error"), self, menu)
        subMenuFixFileNotFoundError.addAction(self.actions['fixFileNotFoundTryFind'])
        subMenuFixFileNotFoundError.addAction(self.actions['fixFileNotFoundRemoveDataRef'])
        subMenuFixHashMismatchError = self._createAndAddSubMenu(self.tr("Fix File Hash Mismatch Error"), self, menu)
        subMenuFixHashMismatchError.addAction(self.actions['fixHashMismatchTryFind'])
        subMenuFixHashMismatchError.addAction(self.actions['fixHashMismatchUpdateHash'])


    def __initContextMenu(self):
        self.buildActions()
        self.__buildContextMenu()
        self.__addContextMenu()

    def __addContextMenu(self):
        assert self.__context_menu is not None, "Context menu is not built"
        self.ui.tableView_items.setContextMenuPolicy(Qt.CustomContextMenu)
        self.connect(self.ui.tableView_items, QtCore.SIGNAL("customContextMenuRequested(const QPoint &)"), self.showContextMenu)

    def showContextMenu(self, pos):
        self.__context_menu.exec_(self.ui.tableView_items.mapToGlobal(pos))



    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()


    def dropEvent(self, event):
        if not event.mimeData().hasUrls:
            event.ignore()
            return

        files = []
        for url in event.mimeData().urls():
            files.append(url.toLocalFile())

        if len(files) <= 0:
            event.ignore()
            return

        event.accept()
        self.__itemsTableTool.acceptDropOfFilesAndDirs(files)


    def __onTableDoubleClicked(self, index):
        if not self.__table_model.isOpenItemActionAllowed(index):
            return
        action = self.actions['openItem']
        action.trigger()


class ItemsTableModel(UnivTableModel):
    def __init__(self, repo):
        super(ItemsTableModel, self).__init__()
        self.repo = repo


    def query(self, query_text, limit=0, page=1):
        uow = self.repo.createUnitOfWork()
        items = []
        try:
            order_by = []
            if query_text is None or query_text.strip()=="":
                items = uow.executeCommand(cmds.GetUntaggedItems(limit, page, order_by))

            else:
                query_tree = query_parser.parse(query_text)
                cmd = cmds.QueryItemsByParseTree(query_tree, limit, page, order_by)
                items = uow.executeCommand(cmd)

        except (errors.YaccError, errors.LexError) as ex:
            raise errors.MsgException(self.tr("Error in the query. Detail info: {}").format(str(ex)))

        finally:
            uow.close()
            self.setObjs(items)

    def isOpenItemActionAllowed(self, index):
        # TODO ...
        return False




# TODO Replace this class with a UnivTableModel ancestor
#class ItemsTableModelOld(QtCore.QAbstractTableModel):
#    '''
#        This class is a model of a table (QTableView) with repository Items.
#    '''
#    ROW_NUMBER = 0
#    ID = 1
#    TITLE = 2
#    IMAGE_THUMB = 3
#    LIST_OF_TAGS = 4
#    STATE = 5 #State of the item (in the means of its integrity)
#    RATING = 6
#
#    def __init__(self, repo, items_lock, user_login):
#        super(ItemsTableModelOld, self).__init__()
#        self.repo = repo
#        self.items = []
#        self._user_login = user_login
#
#
#        #This is a thread for building image thumbnails in the background
#        self.thread = None
#
#        #This is a lock to synchronize threads, reading/writing to self.items collection
#        self.lock = items_lock
#
#        self.query_text = ""
#        self.limit = 0
#        self.page = 1
#
#        self.order_by_column = None
#        self.order_dir = None
#
#
#    def resetSingleRow(self, row):
#        self.resetRowRange(row, row)
#
#    def resetRowRange(self, topRow, bottomRow):
#        topL = self.createIndex(topRow, self.ID)
#        bottomR = self.createIndex(bottomRow, self.RATING)
#        self.emit(QtCore.SIGNAL("dataChanged(const QModelIndex&, const QModelIndex&)"), topL, bottomR)
#
#
#    def _set_user_login(self, user_login):
#        self._user_login = user_login
#
#    def _get_user_login(self):
#        return self._user_login
#
#    user_login = property(_get_user_login, _set_user_login, doc="Current active user login.")
#
#
#    def sort(self, column, order=Qt.AscendingOrder):
#        if column not in [self.ID, self.TITLE, self.RATING]:
#            return
#
#        self.order_by_column = column
#        self.order_dir = order
#
#        self.query(self.query_text, self.limit, self.page)
#
#    def query(self, query_text, limit=0, page=1):
#        '''
#        This function retrieves items from the database.
#        '''
#        self.query_text = query_text
#        self.limit = limit
#        self.page = page
#
#        if self.order_dir == Qt.AscendingOrder:
#            directory = "ASC"
#        else:
#            directory = "DESC"
#
#        order_by = []
#        if self.order_by_column is not None:
#            column = self.order_by_column
#            if column == self.ID:
#                order_by.append(("id", directory))
#            elif column == self.TITLE:
#                order_by.append(("title", directory))
#            #This is not exactly sorting by pure rating, but by fields and their values...
#            elif column == self.RATING:
#                order_by.append(("items_fields_field_id", "DESC"))
#                order_by.append(("items_fields_field_value", directory))
#
#
#        def reset_row(row):
#            self.resetSingleRow(row)
#            QtCore.QCoreApplication.processEvents()
#
#        uow = self.repo.createUnitOfWork()
#        try:
#            if self.thread is not None and self.thread.isRunning():
#                self.thread.interrupt = True
#                self.thread.wait(5*1000)
#
#            if query_text is None or query_text.strip()=="":
#                self.items = uow.executeCommand(cmds.GetUntaggedItems(limit, page, order_by))
#            else:
#                query_tree = query_parser.parse(query_text)
#                cmd = cmds.QueryItemsByParseTree(query_tree, limit, page, order_by)
#                self.items = uow.executeCommand(cmd)
#
#            self.thread = ThumbnailBuilderThread(self, self.repo, self.items, self.lock)
#            self.connect(self.thread, QtCore.SIGNAL("progress"), lambda percents, row: reset_row(row))
#            self.thread.start()
#
#            self.reset()
#
#        except (errors.YaccError, errors.LexError) as ex:
#            raise errors.MsgException(self.tr("Error in the query. Detail info: {}").format(str(ex)))
#
#        finally:
#            uow.close()
#
#
#
#
#
#    def rowCount(self, index=QtCore.QModelIndex()):
#        return len(self.items)
#
#    def columnCount(self, index=QtCore.QModelIndex()):
#        return 7
#
#    def headerData(self, section, orientation, role=Qt.DisplayRole):
#        if orientation == Qt.Horizontal:
#            if role == Qt.DisplayRole:
#                if section == self.ROW_NUMBER:
#                    return self.tr("")
#                elif section == self.ID:
#                    return self.tr("Id")
#                elif section == self.TITLE:
#                    return self.tr("Title")
#                elif section == self.IMAGE_THUMB:
#                    return self.tr("Thumbnail")
#                elif section == self.LIST_OF_TAGS:
#                    return self.tr("Tags")
#                elif section == self.STATE:
#                    return self.tr("State")
#                elif section == self.RATING:
#                    return self.tr("Rating")
#            else:
#                return None
#        elif orientation == Qt.Vertical and role == Qt.DisplayRole:
#            return section + 1
#        else:
#            return None
#
#
#    def data(self, index, role=QtCore.Qt.DisplayRole):
#        if not index.isValid() or not (0 <= index.row() < len(self.items)):
#            return None
#
#        item = self.items[index.row()]
#        column = index.column()
#
#        if role == QtCore.Qt.DisplayRole:
#            if column == self.ROW_NUMBER:
#                return index.row() + 1
#
#            elif column == self.ID:
#                return item.id
#
#            elif column == self.TITLE:
#                return "<b>" + item.title + "</b>" + ("<br/><font>" + item.data_ref.url + "</font>" if item.data_ref else "")
#
#            elif column == self.LIST_OF_TAGS:
#                return item.format_tags()
#
#            elif column == self.STATE:
#                try:
#                    self.lock.lockForRead()
#                    return self.__formatErrorSetShort(item.error)
#                finally:
#                    self.lock.unlock()
#            elif column == self.RATING:
#                #Should display only rating field owned by current active user
#                rating_str = item.getFieldValue(consts.RATING_FIELD, self.user_login)
#                try:
#                    rating = int(rating_str)
#                except:
#                    rating = 0
#                return rating
#
#        elif role == Qt.ToolTipRole:
#            if column == self.ROW_NUMBER:
#                return "Table row number"
#
#            elif column == self.TITLE:
#                if item.data_ref is not None:
#                    s  =  str(item.data_ref.type) + ": " + item.data_ref.url
#                    if  item.data_ref.type == db.DataRef.FILE:
#                        s += os.linesep + self.tr("Checksum (hash): {}").format(item.data_ref.hash)
#                        s += os.linesep + self.tr("File size: {} bytes").format(item.data_ref.size)
#                        s += os.linesep + self.tr("Date hashed: {}").format(item.data_ref.date_hashed)
#                    s += os.linesep + self.tr("Created by: {}").format(item.data_ref.user_login)
#                    s += os.linesep + self.tr("Date created: {}").format(item.data_ref.date_created)
#                    return s
#
#            elif column == self.LIST_OF_TAGS:
#                return item.format_field_vals()
#
#            elif column == self.STATE:
#                try:
#                    self.lock.lockForRead()
#                    return self.__formatErrorSet(item.error)
#                finally:
#                    self.lock.unlock()
#
#
#        elif role == QtCore.Qt.UserRole:
#            if column == self.IMAGE_THUMB and item.data_ref is not None:
#                if item.data_ref.is_image():
#                    pixmap = QtGui.QPixmap()
#                    try:
#                        self.lock.lockForRead()
#                        if len(item.data_ref.thumbnails) > 0:
#                            pixmap.loadFromData(item.data_ref.thumbnails[0].data)
#                    except Exception:
#                        traceback.format_exc()
#                    finally:
#                        self.lock.unlock()
#                    return pixmap
#
#
#        elif role == QtCore.Qt.TextAlignmentRole:
#            if column == self.ROW_NUMBER:
#                return int(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
#
#            if column == self.ID:
#                return int(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
#
#            elif column == self.TITLE:
#                return int(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
#
#        return None
#
#
#    def isOpenItemActionAllowed(self, index):
#        if index.column() == ItemsTableModelOld.RATING:
#            return False
#        else:
#            return True
#
#
#    def __formatErrorSet(self, error_set):
#
#        if error_set is not None:
#            if len(error_set) == 0:
#                s = "No errors"
#            else:
#                s = ""
#                for error in error_set:
#                    if error == db.Item.ERROR_FILE_HASH_MISMATCH:
#                        s += "File contents has changed (hash mismatch)".format(db.Item.ERROR_FILE_HASH_MISMATCH) + os.linesep
#                    elif error == db.Item.ERROR_FILE_NOT_FOUND:
#                        s += "File not found (maybe it was deleted, moved or renamed?)".format(db.Item.ERROR_FILE_NOT_FOUND) + os.linesep
#                if s.endswith(os.linesep):
#                    s = s[:-1]
#        else:
#            s = "Item integrity isn't checked yet"
#
#        return s
#
#    def __formatErrorSetShort(self, error_set):
#        if error_set is None:
#            return ""
#        if len(error_set) <= 0:
#            return self.tr("OK")
#        elif len(error_set) > 0:
#            return helpers.to_commalist(error_set, lambda x: self.__formatErrorShort(x))
#
#    def __formatErrorShort(self, itemErrorCode):
#        if itemErrorCode == db.Item.ERROR_FILE_NOT_FOUND:
#            return self.tr("File not found")
#        elif itemErrorCode == db.Item.ERROR_FILE_HASH_MISMATCH:
#            return self.tr("Hash mismatch")
#        else:
#            assert False, "Unknown error code"
#
#
#
#    def flags(self, index):
#        default_flags = super(ItemsTableModelOld, self).flags(index)
#
#        if index.column() == self.RATING:
#            return Qt.ItemFlags(default_flags | QtCore.Qt.ItemIsEditable)
#        else:
#            return default_flags
#
#    def setData(self, index, value, role=QtCore.Qt.EditRole):
#
#        if role == Qt.EditRole and index.column() == self.RATING:
#            item = self.items[index.row()]
#
#            #Remember old rating value
#            old_value = item.getFieldValue(consts.RATING_FIELD, self.user_login)
#
#            if old_value == value:
#                return False
#
#            item.setFieldValue(consts.RATING_FIELD, value, self.user_login)
#
#            #Store new rating value into database
#            uow = self.repo.createUnitOfWork()
#            try:
#                srcAbsPath = os.path.join(self.repo.base_path, item.data_ref.url) if item.data_ref is not None else None
#                dstRelPath = item.data_ref.url if item.data_ref is not None else None
#                cmd = cmds.UpdateExistingItemCommand(item, srcAbsPath, dstRelPath, self.user_login)
#                uow.executeCommand(cmd)
#                self.emit(QtCore.SIGNAL("dataChanged(const QModelIndex&, const QModelIndex&)"), index, index)
#                return True
#            except:
#                #Restore old value
#                item.setFieldValue(consts.RATING_FIELD, old_value, self.user_login)
#            finally:
#                uow.close()
#
#        return False
