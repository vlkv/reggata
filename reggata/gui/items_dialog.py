# -*- coding: utf-8 -*-
'''
Created on 30.11.2010
@author: vlkv
'''
import os
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt
from reggata.ui.ui_itemsdialog import Ui_ItemsDialog
from reggata.helpers import is_internal, is_none_or_empty, show_exc_info
import reggata.parsers as parsers
from reggata.data.db_schema import DataRef
from reggata.errors import MsgException
from reggata.gui.common_widgets import TextEdit


#TODO: Rename this class to some more meaningful name
class CustomTextEdit(QtGui.QTextEdit):
    '''
        This custom QTextEdit displays with a different style all the text
    which is typed by user.
    '''
    def __init__(self, parent=None):
        super(CustomTextEdit, self).__init__(parent)
        self.setReadOnly(True)

    def event(self, e):
        if e.type() == QtCore.QEvent.KeyPress:
            f = QtGui.QTextCharFormat()
            self.setCurrentCharFormat(f)
            self.setTextColor(Qt.blue)
        return super(CustomTextEdit, self).event(e)


class ItemsDialog(QtGui.QDialog):
    '''
        This dialog is for create/edit a group of repository Items.
    '''

    CREATE_MODE = "CREATE_MODE"
    EDIT_MODE = "EDIT_MODE"

    def __init__(self, parent, repoBasePath, items, mode=EDIT_MODE, same_dst_path=True, completer=None):
        super(ItemsDialog, self).__init__(parent)
        self.ui = Ui_ItemsDialog()
        self.ui.setupUi(self)

        self.repoBasePath = repoBasePath
        self.items = items

        #This is a relative (to repo root) path where all files in the group are located or will be moved to
        self.dst_path = None

        self.group_has_files = False

        #If this field is true, all items will be moved into one selected destination path
        self.same_dst_path = same_dst_path

        self.completer = completer

        if len(items) <= 1:
            raise ValueError(self.tr("ItemsDialog cannot operate with one or zero Item objects."))
        self.ui.label_num_of_items.setText(str(len(items)))


        self.connect(self.ui.buttonBox, QtCore.SIGNAL("accepted()"), self.button_ok)
        self.connect(self.ui.buttonBox, QtCore.SIGNAL("rejected()"), self.button_cancel)
        self.connect(self.ui.buttonSelectLocationDirRelPath, QtCore.SIGNAL("clicked()"), self.selectLocationDirRelPath)

        self.__initCustomWidgets()

        self.setDialogMode(mode)
        self.read()

    def __initCustomWidgets(self):
        self.ui.textEdit_tags = CustomTextEdit()
        self.ui.verticalLayout_tags.addWidget(self.ui.textEdit_tags)

        self.ui.textEdit_fields = CustomTextEdit()
        self.ui.verticalLayout_fields.addWidget(self.ui.textEdit_fields)

        self.ui.plainTextEdit_tags_add = TextEdit(self, completer=self.completer)
        self.ui.verticalLayout_tags_add.addWidget(self.ui.plainTextEdit_tags_add)

        self.ui.plainTextEdit_tags_rm = TextEdit(self, completer=self.completer)
        self.ui.verticalLayout_tags_rm.addWidget(self.ui.plainTextEdit_tags_rm)

        self.ui.plainTextEdit_fields_add = TextEdit(self, completer=self.completer, completer_end_str=": ")
        self.ui.verticalLayout_fields_add.addWidget(self.ui.plainTextEdit_fields_add)

        self.ui.plainTextEdit_fields_rm = TextEdit(self, completer=self.completer)
        self.ui.verticalLayout_fields_rm.addWidget(self.ui.plainTextEdit_fields_rm)


    def setDialogMode(self, mode):
        self.mode = mode
        if mode == ItemsDialog.CREATE_MODE:
            self.ui.label_tags.setVisible(False)
            self.ui.textEdit_tags.setVisible(False)

            self.ui.label_fields.setVisible(False)
            self.ui.textEdit_fields.setVisible(False)

            self.ui.label_tags_rm.setVisible(False)
            self.ui.plainTextEdit_tags_rm.setVisible(False)

            self.ui.label_fields_rm.setVisible(False)
            self.ui.plainTextEdit_fields_rm.setVisible(False)
        elif mode == ItemsDialog.EDIT_MODE:
            pass
        else:
            raise ValueError(self.tr("ItemsDialog does not support DialogMode = {}.").format(mode))





    def read(self):
        if not (len(self.items) > 1):
            return

        if self.mode == ItemsDialog.CREATE_MODE:
            self.__readInCreateMode()

        elif self.mode == ItemsDialog.EDIT_MODE:
            self.__readInEditMode()

        else:
            assert False, "Unknown mode=" + self.mode + " for ItemsDialog"


    def __readInCreateMode(self):
        assert self.mode == ItemsDialog.CREATE_MODE

        for item in self.items:
            if item.data_ref is not None and item.data_ref.type == DataRef.FILE:
                self.group_has_files = True
                break
            else:
                self.group_has_files = False

        assert self.group_has_files, "You cannot CREATE a group of Items without files."


    def __readInEditMode(self):
        assert self.mode == ItemsDialog.EDIT_MODE

        diff_values_html = self.tr("&lt;diff. values&gt;")

        tags_str = ""
        seen_tags = set()
        for i in range(0, len(self.items)):
            for j in range(0, len(self.items[i].item_tags)):
                tag_name = self.items[i].item_tags[j].tag.name
                if tag_name in seen_tags:
                    continue
                has_all = True
                for k in range(0, len(self.items)):
                    if i == k:
                        continue
                    if not self.items[k].has_tag(tag_name):
                        has_all = False
                        break
                seen_tags.add(tag_name)
                if has_all:
                    tags_str = tags_str + "<b>" + tag_name + "</b> "
                else:
                    tags_str = tags_str + '<font color="grey">' + tag_name + "</font> "
        self.ui.textEdit_tags.setText(tags_str)

        fields_str = ""
        seen_fields = set()
        for i in range(0, len(self.items)):
            for j in range(0, len(self.items[i].item_fields)):
                field_name = self.items[i].item_fields[j].field.name
                field_value = self.items[i].item_fields[j].field_value
                if field_name in seen_fields:
                    continue
                all_have_field = True
                all_have_field_value = True
                for k in range(0, len(self.items)):
                    if i == k:
                        continue
                    if not self.items[k].has_field(field_name):
                        all_have_field = False
                    if not self.items[k].has_field(field_name, field_value):
                        all_have_field_value = False
                    if not all_have_field and not all_have_field_value:
                        break

                seen_fields.add(field_name)
                if all_have_field_value:
                    fields_str = fields_str + "<b>" + field_name + ": " + field_value + "</b><br/>"
                elif all_have_field:
                    fields_str = fields_str + '<b>' + field_name + "</b>: " + diff_values_html + "<br/>"
                else:
                    fields_str = fields_str + '<font color="grey">' + field_name + ": " + diff_values_html + "</font><br/>"
        self.ui.textEdit_fields.setText(fields_str)


        same_path, self.dst_path = self.__checkIfAllTheItemsInTheSamePath(self.items)
        if same_path is None:
            self.group_has_files = False
            assert self.dst_path is None, "When same_path is None, dst_path should be None also."
            self.ui.locationDirRelPath.setText(self.tr('<no files>'))
            self.ui.locationDirRelPath.setEnabled(False)
            self.ui.buttonSelectLocationDirRelPath.setEnabled(False)
        elif same_path == 'yes':
            self.group_has_files = True
            assert not is_none_or_empty(self.dst_path)
            self.ui.locationDirRelPath.setText(self.dst_path)
        else:
            self.group_has_files = True
            assert self.dst_path is None, "Because items' files are located in different directories."
            self.ui.locationDirRelPath.setText(self.tr('<different values>'))

    #TODO: would be much better to return (groupHasAtLeastOneFile, filesInTheSamePath, thePath)
    def __checkIfAllTheItemsInTheSamePath(self, items):
        ''' Returns a tuple (answer, thePath), where
            answer - one of ['yes', 'no', None]. 'yes' means that some (maybe even all)
        items are linked with files and all the files are located in the same path.
        'no' - means that some (maybe even all) items are linked with files
        but the files are located in different directories.
        None - means that there are no items with files or len(items) is zero.
            thePath - string with the filesystem path if the answer is 'yes' or
        None in all other cases.
        '''
        dstPath = None
        samePath = None
        for item in items:
            if item.data_ref is None or item.data_ref.type != DataRef.FILE:
                continue

            if dstPath is None:
                dstPath, null = os.path.split(item.data_ref.url)
                samePath = 'yes'
            else:
                path, null = os.path.split(item.data_ref.url)
                if dstPath != path:
                    samePath = 'no'
                    dstPath = None
                    break

        if samePath == 'yes' and len(dstPath.strip()) == 0:
            dstPath = "."

        return (samePath, dstPath)


    def write(self):
        # self.dst_path must be a relative (to root of repo) path to a directory where to put the files.
        # If self.dst_path is none or empty then items will be
        #    a) in CREATE_MODE - put in the root of repo (in the case of recursive adding: tree hierarchy
        # of the source will be copyied);
        #    b) in EDIT_MODE - files of repository will not be moved anywhere.
        if self.group_has_files:
            self.__writeDataRefs()

        self.__writeTagsAndFields()


    def __writeDataRefs(self):
        if self.mode == ItemsDialog.EDIT_MODE and not is_none_or_empty(self.dst_path):
            for item in self.items:
                if (item.data_ref is None) or (item.data_ref.type != DataRef.FILE):
                    continue
                item.data_ref.dstRelPath = os.path.join(
                    self.dst_path,
                    os.path.basename(item.data_ref.url))

        elif self.mode == ItemsDialog.CREATE_MODE:
            # In CREATE_MODE item.data_ref.url for all items will be None at this point
            # We should use item.data_ref.srcAbsPath instead
            for item in self.items:
                if (item.data_ref is None) or (item.data_ref.type != DataRef.FILE):
                    continue

                if self.same_dst_path:
                    tmp = self.dst_path if not is_none_or_empty(self.dst_path) else ""
                    item.data_ref.dstRelPath = os.path.join(
                        tmp,
                        os.path.basename(item.data_ref.srcAbsPath))
                else:
                    if self.dst_path:
                        relPathToFile = os.path.relpath(item.data_ref.srcAbsPath,
                                                        item.data_ref.srcAbsPathToRoot)
                        item.data_ref.dstRelPath = os.path.join(
                            self.dst_path,
                            relPathToFile)
                    else:
                        if is_internal(item.data_ref.srcAbsPath, self.repoBasePath):
                            item.data_ref.dstRelPath = os.path.relpath(
                                item.data_ref.srcAbsPath,
                                self.repoBasePath)
                        else:
                            item.data_ref.dstRelPath = os.path.relpath(
                                item.data_ref.srcAbsPath,
                                item.data_ref.srcAbsPathToRoot)

    def __writeTagsAndFields(self):
        #Processing Tags to add
        text = self.ui.plainTextEdit_tags_add.toPlainText()
        tags, tmp = parsers.definition_parser.parse(text)
        tags_add = set(tags)

        #Processing Tags to remove
        text = self.ui.plainTextEdit_tags_rm.toPlainText()
        tags, tmp = parsers.definition_parser.parse(text)
        tags_rm = set(tags)

        #Processing (Field,Value) pairs to add
        text = self.ui.plainTextEdit_fields_add.toPlainText()
        tmp, fields = parsers.definition_parser.parse(text)
        fieldvals_add = set(fields)

        # Processing Field names to remove
        # NOTE: from parsers point of view it is Tags, but we know that it is Field names.
        text = self.ui.plainTextEdit_fields_rm.toPlainText()
        fieldNames, tmp = parsers.definition_parser.parse(text)
        fields_rm = set(fieldNames)


        #Check that added and removed Tags do not intersect
        intersection = tags_add.intersection(tags_rm)
        if len(intersection) > 0:
            raise ValueError(self.tr("Tags {} cannot be in both add and remove lists.")
                             .format(str(intersection)))

        #Check that added and removed Fields do not intersect
        intersection = set()
        for f, v in fieldvals_add:
            if f in fields_rm:
                intersection.add(f)
        if len(intersection) > 0:
            raise ValueError(self.tr("Fields {} cannot be in both add and remove lists.")
                             .format(str(intersection)))

        for item in self.items:
            #Adding Tags
            for t in tags_add:
                if not item.has_tag(t):
                    item.add_tag(t, item.user_login)

            #Removing Tags
            for t in tags_rm:
                item.remove_tag(t)

            #Adding new (Field,Value) pairs
            for f, v in fieldvals_add:
                item.remove_field(f)
                item.set_field_value(f, v, item.user_login)

            #Removing Fields
            for f in fields_rm:
                item.remove_field(f)



    def selectLocationDirRelPath(self):
        try:
            if self.mode == ItemsDialog.EDIT_MODE and not self.group_has_files:
                raise MsgException(self.tr(
                    "Selected group of items doesn't reference any physical files on filesysem."))

            dir = QtGui.QFileDialog.getExistingDirectory(self,
                self.tr("Select destination path within repository"),
                self.repoBasePath)
            if not dir:
                return
            if not is_internal(dir, self.repoBasePath):
                raise MsgException(self.tr("Chosen directory is out of opened repository."))

            self.dst_path = os.path.relpath(dir, self.repoBasePath)
            self.ui.locationDirRelPath.setText(self.dst_path)

        except Exception as ex:
            show_exc_info(self, ex)



    def button_ok(self):
        try:
            self.write()
            self.accept()

        except Exception as ex:
            show_exc_info(self, ex)

    def button_cancel(self):
        self.reject()
