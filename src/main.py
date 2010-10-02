# -*- coding: utf-8 -*-
'''
Created on 20.08.2010

@author: vlkv
'''

import sqlite3
import os.path
import sys


from PyQt4.QtCore import (Qt, SIGNAL)
from PyQt4.QtGui import (QApplication, QDialog, QLineEdit, QTextBrowser, QVBoxLayout, QPushButton)

class MainWindow(QDialog):

	def __init__(self, parent=None):
		super(MainWindow, self).__init__(parent)
		self.setWindowTitle("datorg - главное окно")
		self.browser = QTextBrowser()
		self.lineedit = QLineEdit("Type an expression and press Enter")
		self.lineedit.selectAll()

		layout = QVBoxLayout()
		layout.addWidget(self.browser)
		layout.addWidget(self.lineedit)
		self.setLayout(layout)

		self.lineedit.setFocus()
		self.connect(self.lineedit, SIGNAL("returnPressed()"), self.updateUi)


		self.button = QPushButton("Eval")
		layout.addWidget(self.button)
		self.connect(self.button, SIGNAL("pressed()"), self.updateUi)


	def updateUi(self):
		try:
			text = self.lineedit.text()
			self.browser.append("{0} = <b>{1}</b>".format(text, eval(text)))
		except:
			self.browser.append("<font color=red>{0} is invalid!</font>".format(text))



if __name__ == '__main__':

	app = QApplication(sys.argv)
	form = MainWindow()
	form.show()
	app.exec_()

#	path = '../test.sqlite'
#	if os.path.isfile(path):
#		conn = sqlite3.connect(path)
#		try:
#			c = conn.cursor()
#			c.execute('''insert into "data"
#				  (uri, size) values ('path_to_file 4', '10243434')''')
#			conn.commit()
#			c.close()
#		except:
#			print 'error: ', sys.exc_info()
#		finally:
#			conn.close()
#
#	else:
#		print 'file not found ', path
