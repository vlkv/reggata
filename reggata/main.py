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
import reggata.helpers as hlp
from reggata.user_config import UserConfig
import reggata.reggata_dir_locator
import reggata.logging_default_conf as logging_default_conf
from reggata.gui.main_window import MainWindow
from gui.user_dialogs_facade import UserDialogsFacade
import urllib
import re


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


def isReggataInstanceRegistered():
    instanceId = UserConfig().get("reggata_instance_id")
    return False if hlp.is_none_or_empty(instanceId) else True


def isUserGaveTheAnswerAboutSendStatistics():
    sendStatistics = UserConfig().get("send_statistics")
    return False if hlp.is_none_or_empty(sendStatistics) else True


def isSendStatisticsAllowed():
    sendStatistics = UserConfig().get("send_statistics")
    return hlp.stringToBool(sendStatistics)


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
        UserConfig().store("send_statistics", sendStatistics)


def registerReggataInstance():
    try:
        timeoutSec = 5
        with urllib.request.urlopen("http://reggata-stats.appspot.com/register", None, timeoutSec) as f:
            response = f.read()
        instanceId = response.decode("utf-8")
        mobj = re.match(r"[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}", instanceId)
        if mobj is None:
            raise Exception("Server returned bad instance id, it doesn't look like UUID: " + instanceId)
        UserConfig().store("reggata_instance_id", mobj.group(0))

    except Exception as ex:
        logger.warning("Could not register Reggata instance, reason: " + str(ex))




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

    if not isReggataInstanceRegistered() and not isUserGaveTheAnswerAboutSendStatistics():
        askUserAboutSendStatistics(mw)

    if isSendStatisticsAllowed() and not isReggataInstanceRegistered():
        registerReggataInstance()


    app.exec_()
    logger.info("========= Reggata finished =========")


if __name__ == '__main__':
    main()
