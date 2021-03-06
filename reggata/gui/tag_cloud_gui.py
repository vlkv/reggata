# -*- coding: utf-8 -*-
'''
Created on 13.11.2010
@author: vlkv
'''
import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui
from PyQt4.QtCore import Qt
import reggata.parsers as parsers
import reggata.statistics as stats
from reggata.helpers import show_exc_info, is_none_or_empty
from reggata.errors import MsgException
from reggata.user_config import UserConfig
from reggata.data.commands import GetRelatedTagsCommand
from reggata.logic.abstract_tool_gui import AbstractToolGui
from reggata.gui.tool_gui import ToolGui


def scale_value(value, src_range, dst_range):
    '''
        Scales 'value' from range [src_range[0], src_range[1]]
    to different range [dst_range[0], dst_range[1]]. If 'value' is out
    from source range, it is aligned on the corresponding boundary of
    destination range.
    '''
    if src_range[0] > src_range[1]:
        raise ValueError("Incorrect range, src_range[0] must be less then src_range[1].")

    if dst_range[0] > dst_range[1]:
        raise ValueError("Incorrect range, dst_range[0] must be less then dst_range[1].")

    result = float(value) * (float(dst_range[0]) - dst_range[1]) / (src_range[0] - src_range[1])
    if result < dst_range[0]:
        result = dst_range[0]
    elif result > dst_range[1]:
        result = dst_range[1]
    return result



class TagCloudGui(ToolGui):
    def __init__(self, parent=None, repo=None):
        super(TagCloudGui, self).__init__(parent)
        self.__tagCloudTextEdit = TagCloudTextEdit(parent, repo)

        self.connect(self.__tagCloudTextEdit,
                     QtCore.SIGNAL("selectedTagsChanged"),
                     self._emitSelectedTagsChanged)

        self.connect(self.__tagCloudTextEdit,
                     QtCore.SIGNAL("selectedKeywordAll"),
                     self._emitSelectedKeywordAll)



        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.__tagCloudTextEdit)
        self.setLayout(layout)

    def reset(self):
        self.__tagCloudTextEdit.reset()

    def _setRepo(self, value):
        self.__tagCloudTextEdit.repo = value
    def _getRepo(self):
        return self.__tagCloudTextEdit.repo
    repo = property(_getRepo, _setRepo)

    def _emitSelectedTagsChanged(self, tags, notTags):
        self.emit(QtCore.SIGNAL("selectedTagsChanged"), tags, notTags)

    def _emitSelectedKeywordAll(self):
        self.emit(QtCore.SIGNAL("selectedKeywordAll"))

    def refresh(self):
        self.__tagCloudTextEdit.refresh()


class TagCloudTextEdit(QtGui.QTextEdit):
    '''
        TagCloudTextEdit is a widget for displaying and interacting with a Cloud of Tags.
    '''
    def __init__(self, parent=None, repo=None):
        super(TagCloudTextEdit, self).__init__(parent)

        #Current word in tag cloud under the mouse cursor
        self.word = None
        self.keywordAll = False

        #This is a list of tuples (tag_name, count_of_items_with_this_tag)
        self.tag_count = None

        self.setMouseTracking(True)
        self.setReadOnly(True)
        self.tags = set()
        self.not_tags = set()
        self._repo = repo

        self.menu = None # TODO: rename to contextMenu

        try:
            self._limit = int(UserConfig().get("tag_cloud.limit", 0))
            if self._limit < 0:
                raise ValueError()
        except:
            self._limit = 0

        palette = QtGui.QApplication.palette()
        self.bg_color = UserConfig().get("tag_cloud.tag_background_color", QtGui.QColor(230, 230, 230).name())
        self.text_color = UserConfig().get("tag_cloud.tag_text_color", palette.text().color().name())
        self.hl_text_color = UserConfig().get("tag_cloud.tag_highlighted_text_color", QtGui.QColor("blue"))

    def _set_limit(self, value):
        self._limit = value
        self.refresh()
    def _get_limit(self):
        return self._limit
    limit = property(_get_limit, _set_limit)


    def _setRepo(self, value):
        self._repo = value
        self.reset()
    def _getRepo(self):
        return self._repo
    repo = property(_getRepo, _setRepo)



    def refresh(self):
        #TODO Implement filtering by user login
        if self.repo is None:
            self.setText("")
            return

        if self.keywordAll:
            self.setText("")
            return

        uow = self.repo.createUnitOfWork()
        try:
            cmd = GetRelatedTagsCommand(list(self.tags), limit=self.limit)
            tags = uow.executeCommand(cmd)

            self.tag_count = tags

            tags_sorted = sorted(tags, key=lambda tag : tag.c, reverse=True)
            sizes = dict()
            size_max = 6
            i = 0
            while i < size_max and i < len(tags_sorted):
                sizes[tags_sorted[i].c] = size_max - i
                i += 1

            text = ""
            for tag in tags:
                font_size = sizes.get(tag.c, 0)

                # We should NOT escape tag names here
                text = text + " " + TagCloudTextEdit.formatTag(self.bg_color, font_size,
                                                               self.text_color, tag.name)

            # 'ALL' is a special keyword that selects all the items from the repo
            text = TagCloudTextEdit.formatTag(self.bg_color, 0, self.text_color, "ALL") + text

            self.setText(text)
        finally:
            uow.close()


    @staticmethod
    def formatTag(bgColor, fontSize, textColor, tagName):
        return '<font style="BACKGROUND-COLOR: {0}" size="+{1}" color="{2}">'\
            .format(bgColor, fontSize, textColor) + tagName + '</font>'


    def reset(self):
        self.tags.clear()
        self.not_tags.clear()
        self.keywordAll = False
        self.refresh()


    def event(self, e):
        if e.type() == QtCore.QEvent.Enter:
            pass
        elif e.type() == QtCore.QEvent.Leave:
            #Colour previous word into default color
            cursor1 = self.textCursor()
            cursor1.select(QtGui.QTextCursor.Document)
            fmt = QtGui.QTextCharFormat()
            fmt.setForeground(QtGui.QBrush(QtGui.QColor(self.text_color)))
            cursor1.mergeCharFormat(fmt)
            self.word = None
        elif self.word is not None and self.tag_count is not None and e.type() == QtCore.QEvent.ToolTip:

            if self.word == "ALL" and self.keywordAll:
                QtGui.QToolTip.showText(e.globalPos(), self.tr("Select all items"))
            else:
                #Show number of items for tag name under the mouse cursor
                for tag_name, tag_count in self.tag_count:
                    if tag_name == self.word:
                        QtGui.QToolTip.showText(e.globalPos(), str(tag_count))
                        break
        return super(TagCloudTextEdit, self).event(e)




    def mouseMoveEvent(self, e):
        #Get current word under cursor
        cursor = self.cursorForPosition(e.pos())
        cursor.select(QtGui.QTextCursor.WordUnderCursor)
        word = cursor.selectedText()

        #print("pos={}".format(cursor.position()))
        if word == "ALL" and cursor.position() <= 3:
            self.keywordAll = True
        else:
            self.keywordAll = False

        # If current word has changed or cleared --- set default formatting
        if word != self.word or is_none_or_empty(word):
            cursor1 = self.textCursor()
            cursor1.select(QtGui.QTextCursor.Document)
            fmt = QtGui.QTextCharFormat()
            fmt.setForeground(QtGui.QBrush(QtGui.QColor(self.text_color)))
            cursor1.mergeCharFormat(fmt)
            self.word = None

        # If current word has changed --- highlight it
        if word != self.word:
            fmt = QtGui.QTextCharFormat()
            fmt.setForeground(QtGui.QBrush(QtGui.QColor(self.hl_text_color)))
            cursor.mergeCharFormat(fmt)
            self.word = word

        # NOTE: There is a problem when tag contains a spaces or dashes (and other special chars).
        # word is detected incorrectly in such a case.
        # TODO: Have to fix this problem
        return super(TagCloudTextEdit, self).mouseMoveEvent(e)


    def mouseDoubleClickEvent(self, e):
        if self.keywordAll:
            self.emit(QtCore.SIGNAL("selectedKeywordAll"))
            self.refresh()
            stats.sendEvent("tag_cloud.all_clicked")
            return

        if not is_none_or_empty(self.word):
            word = self.word
            if parsers.query_tokens.needs_quote(word):
                word = parsers.util.quote(word)

            if e.modifiers() == Qt.ControlModifier:
                self.not_tags.add(word)
            else:
                self.tags.add(word)
            self.emit(QtCore.SIGNAL("selectedTagsChanged"), self.tags, self.not_tags)
            self.refresh()
            stats.sendEvent("tag_cloud.tag_clicked")
            return


    def contextMenuEvent(self, e):
        if not self.menu:
            self.menu = QtGui.QMenu()
            self.action_and_tag = self.menu.addAction(self.tr("AND Tag"))
            self.connect(self.action_and_tag, QtCore.SIGNAL("triggered()"), self._and_tag)

            self.action_and_not_tag = self.menu.addAction(self.tr("AND NOT Tag"))
            self.connect(self.action_and_not_tag, QtCore.SIGNAL("triggered()"), self._and_not_tag)

            self.action_set_limit = self.menu.addAction(self.tr("Limit number of tags"))
            self.connect(self.action_set_limit, QtCore.SIGNAL("triggered()"), self._onSetLimitActionTriggered)
        self.menu.exec_(e.globalPos())

    def _and_tag(self):
        '''
            Adds a tag to the query (from context menu).
        '''
        try:
            sel_text = self.textCursor().selectedText()
            if not sel_text:
                sel_text = self.word
            if not sel_text:
                raise MsgException(self.tr("There is no selected text in tag cloud."))
            if parsers.query_tokens.needs_quote(sel_text):
                sel_text = parsers.util.quote(sel_text)
            self.tags.add(sel_text)
            self.emit(QtCore.SIGNAL("selectedTagsChanged"), self.tags, self.not_tags)
            self.refresh()
            stats.sendEvent("tag_cloud.ctx_menu.and_tag")
        except Exception as ex:
            show_exc_info(self, ex)

    def _and_not_tag(self):
        '''
            Adds a tag negation (NOT Tag) to the query (from context menu).
        '''
        try:
            sel_text = self.textCursor().selectedText()
            if not sel_text:
                sel_text = self.word
            if not sel_text:
                raise MsgException(self.tr("There is no selected text in tag cloud."))
            if parsers.query_tokens.needs_quote(sel_text):
                sel_text = parsers.util.quote(sel_text)
            self.not_tags.add(sel_text)
            self.emit(QtCore.SIGNAL("selectedTagsChanged"), self.tags, self.not_tags)
            self.refresh()
            stats.sendEvent("tag_cloud.ctx_menu.and_not_tag")
        except Exception as ex:
            show_exc_info(self, ex)

    def _onSetLimitActionTriggered(self):
        i, ok = QtGui.QInputDialog.getInteger(self, self.tr("Reggata input dialog"), \
            self.tr("Enter new value for maximum number of tags in the cloud (0 - unlimited)."), \
            value=self.limit, min=0, max=1000000000)
        if ok:
            self.limit = i
            UserConfig().store("tag_cloud.limit", i)
        stats.sendEvent("tag_cloud.ctx_menu.set_limit")
