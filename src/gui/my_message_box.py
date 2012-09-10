'''
Created on 21.08.2012
@author: vlkv
'''
import PyQt4.QtGui as QtGui



class MyMessageBox(QtGui.QMessageBox):
    '''
        This MessageBox window can be resized with a mouse. Standard QMessageBox
    could not. Solution was taken from here: 
    http://stackoverflow.com/questions/2655354/how-to-allow-resizing-of-qmessagebox-in-pyqt4
    '''
    def __init__(self, parent=None):
        super(MyMessageBox, self).__init__(parent)    
        self.setSizeGripEnabled(True)
        self.addButton(QtGui.QMessageBox.Ok)
        self.setDefaultButton(QtGui.QMessageBox.Ok)
        self.setEscapeButton(QtGui.QMessageBox.Ok)

    def event(self, e):
        result = QtGui.QMessageBox.event(self, e)

        self.setMinimumHeight(0)
        self.setMaximumHeight(16777215)
        self.setMinimumWidth(0)
        self.setMaximumWidth(16777215)
        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

        textEdit = self.findChild(QtGui.QTextEdit)
        if textEdit != None :
            textEdit.setMinimumHeight(0)
            textEdit.setMaximumHeight(16777215)
            textEdit.setMinimumWidth(0)
            textEdit.setMaximumWidth(16777215)
            textEdit.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
            
        return result


