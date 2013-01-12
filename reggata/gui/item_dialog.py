# -*- coding: utf-8 -*-
'''
Created on 15.10.2010
@author: vlkv
'''
import os
import PyQt4.QtGui as QtGui
import PyQt4.QtCore as QtCore
from reggata.ui.ui_itemdialog import Ui_ItemDialog
import reggata.consts as consts
from reggata.data.db_schema import Item, DataRef, Tag, Item_Tag, Field, Item_Field
from reggata.helpers import show_exc_info, is_none_or_empty, is_internal
from reggata.parsers import definition_parser, definition_tokens
from reggata.parsers.util import quote
from reggata.errors import MsgException
from reggata.gui.common_widgets import TextEdit


class ItemDialog(QtGui.QDialog):
    '''
        This dialog is for create/edit/view single repository Item.
    '''

    CREATE_MODE = "CREATE_MODE"
    EDIT_MODE = "EDIT_MODE"
    VIEW_MODE = "VIEW_MODE"

    def __init__(self, parent, item, repoBasePath, mode, completer=None):
        super(ItemDialog, self).__init__(parent)
        self.ui = Ui_ItemDialog()
        self.ui.setupUi(self)

        self.repoBasePath = repoBasePath

        self.completer = completer

        #Adding my custom widgets to dialog
        self.ui.plainTextEdit_fields = TextEdit(self, self.completer, completer_end_str=": ")
        self.ui.verticalLayout_text_edit_fields.addWidget(self.ui.plainTextEdit_fields)

        self.ui.plainTextEdit_tags = TextEdit(self, self.completer)
        self.ui.verticalLayout_text_edit_tags.addWidget(self.ui.plainTextEdit_tags)

        if type(item) != Item:
            raise TypeError(self.tr("Argument item should be an instance of Item class."))

        self.parent = parent
        self.mode = mode
        self.item = item
        self.connect(self.ui.buttonBox, QtCore.SIGNAL("accepted()"), self.button_ok)
        self.connect(self.ui.buttonBox, QtCore.SIGNAL("rejected()"), self.button_cancel)
        self.connect(self.ui.pushButtonAddDataRef, QtCore.SIGNAL("clicked()"), self.buttonAddDataRef)
        self.connect(self.ui.pushButtonRemoveDataRef, QtCore.SIGNAL("clicked()"), self.buttonRemoveDataRef)
        self.connect(self.ui.pushButtonMoveFile, QtCore.SIGNAL("clicked()"), self.buttonMoveFile)

        self.read()


    def read(self):
        '''
        Function updates all dialog GUI elements according to self.item object data.
        '''
        self.ui.lineEdit_id.setText(str(self.item.id))
        self.ui.lineEdit_user_login.setText(self.item.user_login)
        self.ui.lineEdit_title.setText(self.item.title)


        if self.item.data_ref:
            #Make an absolute path to the DataRef file
            fileAbsPath = self.item.data_ref.url
            if not os.path.isabs(fileAbsPath):
                fileAbsPath = os.path.join(self.repoBasePath, fileAbsPath)
            if not os.path.exists(fileAbsPath):
                self.ui.fileAbsPath.setText("FILE NOT FOUND: " + fileAbsPath)
            else:
                self.ui.fileAbsPath.setText(fileAbsPath)

            locationDirRelPath = ""
            if self.mode == ItemDialog.EDIT_MODE or self.mode == ItemDialog.VIEW_MODE:
                #Make a relative path to the directory where DataRef file is located
                locationDirRelPath = os.path.dirname(self.item.data_ref.url)
                locationDirRelPath = "." \
                    if locationDirRelPath.strip() == "" \
                    else "." + os.path.sep + locationDirRelPath
            self.ui.fileLocationDirRelPath.setText(locationDirRelPath)


        #Displaying item's list of field-values
        s = ""
        for itf in self.item.item_fields:
            #Processing reserved fields
            if itf.field.name in consts.RESERVED_FIELDS:
                if itf.field.name == consts.NOTES_FIELD:
                    self.ui.plainTextEdit_notes.setPlainText(itf.field_value)
                elif itf.field.name == consts.RATING_FIELD:
                    try:
                        rating = int(itf.field_value)
                    except:
                        rating = 0
                    self.ui.spinBox_rating.setValue(rating)
                else:
                    raise MsgException(
                        self.tr("Unknown reserved field name '{}'").format(itf.field.name))
            #Processing all other fields
            else:
                name = quote(itf.field.name) if definition_tokens.needs_quote(itf.field.name) \
                    else itf.field.name
                value = quote(itf.field_value) if definition_tokens.needs_quote(itf.field_value) \
                    else itf.field_value
                s = s + name + ": " + value + os.linesep
        self.ui.plainTextEdit_fields.setPlainText(s)

        #Displaying item's list of tags
        s = ""
        for itg in self.item.item_tags:
            tag_name = itg.tag.name
            s = s + (quote(tag_name) if definition_tokens.needs_quote(tag_name) else tag_name) + " "
        self.ui.plainTextEdit_tags.setPlainText(s)



    def write(self):
        '''Writes all data from dialog GUI elements to the self.item object.'''

        self.item.title = self.ui.lineEdit_title.text()

        #Processing Tags
        del self.item.item_tags[:]
        text = self.ui.plainTextEdit_tags.toPlainText()
        tags, _tmp = definition_parser.parse(text)
        for t in tags:
            tag = Tag(name=t)
            item_tag = Item_Tag(tag)
            item_tag.user_login = self.item.user_login
            self.item.item_tags.append(item_tag)

        #Processing Fields
        del self.item.item_fields[:]
        text = self.ui.plainTextEdit_fields.toPlainText()
        _tmp, fields = definition_parser.parse(text)
        for (f, v) in fields:
            if f in consts.RESERVED_FIELDS:
                raise MsgException(self.tr("Field name '{}' is reserved.").format(f))
            field = Field(name=f)
            item_field = Item_Field(field, v)
            item_field.user_login = self.item.user_login
            self.item.item_fields.append(item_field)

        #Processing reserved field NOTES_FIELD
        notes = self.ui.plainTextEdit_notes.toPlainText()
        if not is_none_or_empty(notes):
            field = Field(name=consts.NOTES_FIELD)
            item_field = Item_Field(field, notes)
            item_field.user_login = self.item.user_login
            self.item.item_fields.append(item_field)

        #Processing reserved field RATING_FIELD
        rating = self.ui.spinBox_rating.value()
        if rating > 0:
            field = Field(name=consts.RATING_FIELD)
            item_field = Item_Field(field, rating)
            item_field.user_login = self.item.user_login
            self.item.item_fields.append(item_field)

        #Processing DataRef object
        if self.item.data_ref is not None:
            self.__writeDataRef()


    def __writeDataRef(self):
        assert(self.item.data_ref is not None)

        srcAbsPath = self.ui.fileAbsPath.text()

        isFileInsideRepo = is_internal(srcAbsPath, self.repoBasePath)

        dirRelPath = self.ui.fileLocationDirRelPath.text()
        if not is_none_or_empty(dirRelPath):
            #File will be copied to user selected location
            filename = os.path.basename(srcAbsPath)
            dstRelPath = os.path.join(dirRelPath, filename)
        elif isFileInsideRepo:
            #File will stay where it is
            dstRelPath = os.path.relpath(srcAbsPath, self.repoBasePath)
        else:
            #File will be copied to the repository root
            dstRelPath = os.path.basename(srcAbsPath)

        self.item.data_ref.srcAbsPath = os.path.normpath(srcAbsPath)
        self.item.data_ref.dstRelPath = os.path.normpath(dstRelPath)


    def button_ok(self):
        try:
            if self.mode == ItemDialog.VIEW_MODE:
                self.accept()

            elif self.mode == ItemDialog.CREATE_MODE or self.mode == ItemDialog.EDIT_MODE:
                self.write()
                self.item.check_valid()
                self.accept()

            else:
                raise ValueError(self.tr("self.mode has bad value."))

        except Exception as ex:
            show_exc_info(self, ex)


    def button_cancel(self):
        self.reject()


    def buttonAddDataRef(self):

        file = QtGui.QFileDialog.getOpenFileName(self, self.tr("Select a file to link with the Item."))
        if is_none_or_empty(file):
            return

        #Suggest a title for the Item, if it has not any title yet
        title = self.ui.lineEdit_title.text()
        if is_none_or_empty(title):
            self.ui.lineEdit_title.setText(os.path.basename(file))

        data_ref = DataRef(type=DataRef.FILE, url=file)
        self.item.data_ref = data_ref

        assert(os.path.isabs(data_ref.url))
        self.ui.fileAbsPath.setText(data_ref.url)


    def buttonRemoveDataRef(self):
        self.item.data_ref = None
        self.item.data_ref_id = None
        self.ui.fileAbsPath.setText(None)
        self.ui.fileLocationDirRelPath.setText(None)


    def buttonMoveFile(self):
        try:
            if self.item.data_ref is None:
                raise Exception(self.tr("You must add a Data Reference first."))

            directory = QtGui.QFileDialog.getExistingDirectory(
                self,
                self.tr("Select destination path within repository"),
                self.repoBasePath)

            if is_none_or_empty(directory):
                return

            if not is_internal(directory, self.repoBasePath):
                raise MsgException(self.tr("Chosen directory is out of active repository."))
            else:
                new_dst_path = os.path.relpath(directory, self.repoBasePath)
                if new_dst_path != ".":
                    new_dst_path = "." + os.path.sep + new_dst_path

                self.ui.fileLocationDirRelPath.setText(new_dst_path)

        except Exception as ex:
            show_exc_info(self, ex)
