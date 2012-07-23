# -*- coding: utf-8 -*-
'''
Created on 11.07.2012

@author: vlkv
'''
import PyQt4.QtGui as QtGui
import PyQt4.QtCore as QtCore
from PyQt4.QtCore import Qt
import parsers
from commands import GetNamesOfAllTagsAndFields
from helpers import is_none_or_empty



class TextEdit(QtGui.QTextEdit):
    '''Modified QTextEdit, that supports Completer class. When user presses shortcut Ctrl+Space,
    it shows a completer (if such exists) that helps user to enter tag/field names.'''
    
    def __init__(self, parent=None, completer=None, completer_end_str=" ", one_line=False):
        super(TextEdit, self).__init__(parent)        
        self.completer = completer
        self.completer_end_str = completer_end_str
        self.setPlainText("")
        
        self.one_line = one_line
        if one_line:
            #In this case TextEdit should emulate QLineEdit behaviour
            self.setWordWrapMode(QtGui.QTextOption.NoWrap)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setTabChangesFocus(True)
            self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
            
            #TODO I dont like this:
            self.setFixedHeight(QtGui.QLineEdit().sizeHint().height())
            
            
    
    def set_completer(self, completer):
        self.completer = completer    
    
    def text(self):
        '''This is for QLineEdit behaviour.'''
        return self.toPlainText()
    
    def show_completer(self):
        if self.completer is not None:
            rect = self.cursorRect()
            point = rect.bottomLeft()
            self.completer.move(self.mapToGlobal(point))
            
            self.completer.end_str = self.completer_end_str
            
            
            self.completer.show()
            self.completer.setFocus(Qt.PopupFocusReason)
      
    def keyPressEvent(self, event):
        
        cursor = self.textCursor()
        cursor.select(QtGui.QTextCursor.WordUnderCursor)
        word = cursor.selectedText()
        word = word if not is_none_or_empty(word) else ""
        
        if self.completer is not None and \
        event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Space:        
            self.completer.filter(word)
            self.show_completer()
            super(TextEdit, self).keyPressEvent(event)                        
            #TODO When user press Ctrl+Space, completer is shown, but TextEdit cursor becomes hidden! Why?
            
        elif self.one_line and event.key() in [Qt.Key_Enter, Qt.Key_Return]:
            #This signal is for QLineEdit behaviour
            self.emit(QtCore.SIGNAL("returnPressed()"))
            
        elif event.key() in [Qt.Key_Backspace, Qt.Key_Delete, 
                             Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right,
                             Qt.Key_End, Qt.Key_Home, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Control]:
            super(TextEdit, self).keyPressEvent(event)
            
        elif len(word) > 0:
            self.completer.filter(word)            
            if self.completer.count() > 0:
                self.show_completer()
            super(TextEdit, self).keyPressEvent(event)
                        
        else:
            super(TextEdit, self).keyPressEvent(event)
            
        
    def focusInEvent(self, event):
        #completer may be shared between multilple text edit widgets
        if self.completer is not None:
            self.completer.set_widget(self)
        super(TextEdit, self).focusInEvent(event)
        



class Completer(QtGui.QListWidget):
    '''This class is a popup list widget with tag/field names.
    It should help user to enter tags/fields. Completer should be used with TextEdit class.
    '''    
    def __init__(self, repo, parent=None, end_str=" "):
        super(Completer, self).__init__(parent)
        self.setWindowFlags(Qt.Popup)
        #self.setWindowModality(Qt.NonModal)
        
        self.repo = repo
        self.words = []
        self.widget = None #This is a text edit widget for which completion is perfomed
        
        self.end_str = end_str #This string is placed after every inserted name
                
        self.connect(self, QtCore.SIGNAL("itemActivated(QListWidgetItem *)"), self.submit_word)
    
        self.populate_words()
    
    def set_widget(self, widget):
        if self.widget:
            self.disconnect(self.widget, QtCore.SIGNAL("textChanged()"), self.widget_text_changed)             
            
        self.widget = widget
        self.connect(self.widget, QtCore.SIGNAL("textChanged()"), self.widget_text_changed)
    
    def event(self, e):
        #print("Completer {}".format(type(e)))
        
        #This hides the completer (self) when user clicks somewhere outside
        if e.type() == QtCore.QEvent.MouseButtonPress:
            self.hide()
            
        return super(Completer, self).event(e)
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
            
        elif event.key() in [Qt.Key_Enter, Qt.Key_Return, Qt.Key_Up, Qt.Key_Down]:
            super(Completer, self).keyPressEvent(event)
            
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Space:
            #Refresh tag/field names from database
            self.populate_words()
            self.widget_text_changed()
            
        elif event.key() == Qt.Key_Backspace:
            cursor = self.widget.textCursor()
            cursor.deletePreviousChar()
        
        elif event.key() in [Qt.Key_Left]:
            cursor = self.widget.textCursor()
            #cursor.setVisualNavigation(True)
            cursor.movePosition(QtGui.QTextCursor.Left)
            self.widget.setTextCursor(cursor)
            
            
        elif event.key() in [Qt.Key_Right]:
            cursor = self.widget.textCursor()
            #cursor.setVisualNavigation(True)
            cursor.movePosition(QtGui.QTextCursor.Right)
            self.widget.setTextCursor(cursor)
            
        else:
            text = event.text()
            cursor = self.widget.textCursor()
            cursor.insertText(text)
            
    def submit_word(self, item):
        if self.widget is not None and item is not None:            
            cursor = self.widget.textCursor()
            cursor.select(QtGui.QTextCursor.WordUnderCursor)
            word = item.text()
            if parsers.query_parser.needs_quote(word):
                word = parsers.util.quote(word)
            cursor.insertText(word + self.end_str)
        self.hide()
        
    def populate_words(self):
        if self.repo is None:
            raise ValueError(self.tr("Completer does'n connected to repository."))

        uow = self.repo.create_unit_of_work()
        try:
            self.words = uow.executeCommand(GetNamesOfAllTagsAndFields())
        finally:
            uow.close()
    
    def widget_text_changed(self):
        if self.widget is not None:
            cursor = self.widget.textCursor()
            cursor.select(QtGui.QTextCursor.WordUnderCursor)
            word =  cursor.selectedText()
            if is_none_or_empty(word):
                self.hide()
            self.filter(word)
            if self.count() <= 0:
                self.hide()
    
    def filter(self, prefix):
        self.clear()
        for (word,) in self.words:
            if word.startswith(prefix):
                self.addItem(word)
        self.setCurrentRow(0)
        #TODO not very smart search! Very expensive.
                
        