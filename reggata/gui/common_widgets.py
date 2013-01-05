'''
Created on 11.07.2012

@author: vlkv
'''
import logging
import PyQt4.QtGui as QtGui
import PyQt4.QtCore as QtCore
from PyQt4.QtCore import Qt
import reggata.parsers as parsers
from reggata.helpers import is_none_or_empty
import reggata.consts as consts
from reggata.data.commands import GetNamesOfAllTagsAndFields
from reggata.gui.my_message_box import MyMessageBox
import os


logger = logging.getLogger(consts.ROOT_LOGGER + "." + __name__)


class FileDialog(QtGui.QFileDialog):
    '''
        This FileDialog should allow user to select multiple files and directories. 
    QFileDialog cannot do this.
    '''
    #TODO: finish this class...
    def __init__(self, *args):
        super(FileDialog, self).__init__(*args)
        self.setOption(self.DontUseNativeDialog, True)
        self.setFileMode(self.ExistingFiles)
        btns = self.findChildren(QtGui.QPushButton)
        self.openBtn = [x for x in btns if 'open' in str(x.text()).lower()][0]
        self.openBtn.clicked.disconnect()
        self.openBtn.clicked.connect(self.openClicked)
        self.tree = self.findChild(QtGui.QTreeView)

    def openClicked(self):
        inds = self.tree.selectionModel().selectedIndexes()
        files = []
        for i in inds:
            if i.column() == 0:
                files.append(os.path.join(str(self.directory().absolutePath()),str(i.data().toString())))
        self.selectedFiles = files
        self.hide()

    def filesSelected(self):
        return self.selectedFiles       

 
   

class WaitDialog(QtGui.QDialog):    
    
    def __init__(self, parent=None, indeterminate=False):
        super(WaitDialog, self).__init__(parent)
        self.setModal(True)
        self.setWindowTitle("Reggata")
        
        vbox = QtGui.QVBoxLayout()
        
        self.msg_label = QtGui.QLabel(self.tr("Please, wait..."))
        vbox.addWidget(self.msg_label)
        
        self.progress_bar = QtGui.QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        vbox.addWidget(self.progress_bar)
        
        if indeterminate:
            self.progress_bar.setTextVisible(False)
            self.timer = QtCore.QTimer()
            self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.indeterminate_timer)
            self.timer.start(100)
        
        self.setLayout(vbox)
    
    def startWithWorkerThread(self, thread):
        if consts.DEBUG:
            # Breakpoints do not work in other threads. 
            # If you want to debug code of worker background threads, set consts.DEBUG to True
            thread.run()
        else:
            thread.start()
            thread.wait(1000)
            if thread.isRunning():
                self.exec_()
    
    def indeterminate_timer(self):
        value = self.progress_bar.value()
        value = value + int((self.progress_bar.maximum() - self.progress_bar.minimum())/5.0)
        self.progress_bar.setValue(value if value <= self.progress_bar.maximum() \
                                   else self.progress_bar.minimum())
        
    
    def exception(self, exceptionInfo):
        ''' Displays exceptionInfo text in modal message box and rejects WaitDialog. 
        exceptionInfo - is a string containing a text about the raised exception.
        
        This slot is usually connected to the 'exception' signal, emitted from a 
        worker thread.'''
        mb = MyMessageBox(self)
        mb.setWindowTitle(self.tr("Error"))
        mb.setText(self.tr("Operation cannot proceed because of the raised exception."))
        mb.setDetailedText(exceptionInfo)
        mb.exec_()
        
        self.reject()
        
    def closeEvent(self, close_event):
        close_event.ignore() # Disable close button (X) of the dialog.
        
    def set_progress(self, percent_completed):
        '''This slot is called to display progress in percents.'''
        logger.debug("Completed {}%".format(percent_completed))
        self.progress_bar.setValue(percent_completed)


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
        '''
            This is for QLineEdit behaviour.
        '''
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
    '''
        This class is a popup list widget with tag/field names.
    It should help user to enter tags/fields. Completer should be used with TextEdit class.
    '''    
    def __init__(self, repo, parent=None, end_str=" "):
        super(Completer, self).__init__(parent)
        self.setWindowFlags(Qt.Popup)
        
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

        uow = self.repo.createUnitOfWork()
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
                
        