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

Created on 21.01.2012

@author: vlkv
'''
import os.path
import sys
import codecs
import logging.config
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QApplication
from PyQt4.QtCore import QCoreApplication
import reggata.consts as consts
import reggata.statistics as stats
from reggata.user_config import UserConfig
import reggata.reggata_dir_locator
import reggata.logging_default_conf as logging_default_conf
from reggata.gui.main_window import MainWindow
from gui.user_dialogs_facade import UserDialogsFacade


logger = logging.getLogger(consts.ROOT_LOGGER + "." + __name__)


def configureLogging():
    if not os.path.exists(consts.LOGGING_CONFIG_FILE):
        with codecs.open(consts.LOGGING_CONFIG_FILE, "w", "utf-8") as f:
            text = logging_default_conf.loggingDefaultConf
            f.write(text)

    logging.config.fileConfig(consts.LOGGING_CONFIG_FILE)


def configureConfigDir():
    if not os.path.exists(consts.USER_CONFIG_DIR):
        os.makedirs(consts.USER_CONFIG_DIR)


def configureTmpDir():
    if not os.path.exists(consts.DEFAULT_TMP_DIR):
        os.makedirs(consts.DEFAULT_TMP_DIR)


def configureTranslations(app):
    qtr = QtCore.QTranslator(app)
    language = UserConfig().get("language")
    if language:
        qm_filename = "reggata_{}.qm".format(language)

        reggataDir = reggata.reggata_dir_locator.modulePath()
        logger.debug("reggataDir is " + reggataDir)

        isQmLoaded = qtr.load(qm_filename, os.path.join(reggataDir, "reggata", "locale"))
        if not isQmLoaded:
            isQmLoaded = qtr.load(qm_filename, os.path.join(reggataDir, "locale"))

        if isQmLoaded:
            QtCore.QCoreApplication.installTranslator(qtr)
        else:
            logger.warning("Cannot find translation file {}.".format(qm_filename))




def askUserAboutSendStatistics(mainWindow):
    title = "Reggata"
    question = QCoreApplication.translate("main", "Do you want to help make Reggata better by automatically sending usage statistics?", None, QCoreApplication.UnicodeUTF8)
    res = UserDialogsFacade().execGetYesNoAnswerDialog(mainWindow, title, question)
    sendStatistics = None
    if res == QtGui.QMessageBox.Yes:
        sendStatistics = True
    elif res == QtGui.QMessageBox.No:
        sendStatistics = False
    if sendStatistics is not None:
        stats.setSendStatistics(sendStatistics)




def main():
    configureConfigDir()
    configureTmpDir()
    configureLogging()

    logger.info("========= Reggata started =========")
    logger.debug("pyqt_version = {}".format(QtCore.PYQT_VERSION_STR))
    logger.debug("qt_version = {}".format(QtCore.QT_VERSION_STR))
    logger.debug("current dir is " + os.path.abspath("."))

    app = QApplication(sys.argv)

    configureTranslations(app)

    mw = MainWindow()
    mw.show()

    if not stats.isReggataInstanceRegistered() and not stats.isUserGaveTheAnswerAboutSendStatistics():
        askUserAboutSendStatistics(mw)

    if stats.isSendStatisticsAllowed() and not stats.isReggataInstanceRegistered():
        stats.registerReggataInstance()

    stats.sendEvent("reggata_started")

    app.exec_()
    logger.info("========= Reggata finished =========")


if __name__ == '__main__':
    main()
