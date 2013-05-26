'''
Created on 26.05.2013
@author: vlkv
'''
from threading import Thread
import urllib
import reggata.helpers as hlp
from reggata.user_config import UserConfig
from reggata import consts
import logging
import re


logger = logging.getLogger(consts.ROOT_LOGGER + "." + __name__)


def reggataInstanceId():
    return UserConfig().get("reggata_instance_id")


def isReggataInstanceRegistered():
    instanceId = reggataInstanceId()
    return False if hlp.is_none_or_empty(instanceId) else True


def registerReggataInstance():
    try:
        timeoutSec = 5
        with urllib.request.urlopen(consts.STATISTICS_SERVER + "/register_app", None, timeoutSec) as f:
            response = f.read()
        instanceId = response.decode("utf-8")
        mobj = re.match(r"[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}", instanceId)
        if mobj is None:
            raise Exception("Server returned bad instance id, it doesn't look like UUID: " + instanceId)
        UserConfig().store("reggata_instance_id", mobj.group(0))

    except Exception as ex:
        logger.warning("Could not register Reggata instance, reason: " + str(ex))


def isUserGaveTheAnswerAboutSendStatistics():
    sendStatistics = UserConfig().get("send_statistics")
    return False if hlp.is_none_or_empty(sendStatistics) else True


def setSendStatistics(sendStatistics):
    UserConfig().store("send_statistics", sendStatistics)


def isSendStatisticsAllowed():
    sendStatistics = UserConfig().get("send_statistics")
    return hlp.stringToBool(sendStatistics)


def _sendEvent(instanceId, name):
    print("_sendEvent started")
    timeoutSec = 5
    with urllib.request.urlopen(consts.STATISTICS_SERVER + "/put_event?app_instance_id={}&name={}"
                           .format(instanceId, name),
                           None, timeoutSec) as f:
        response = f.read()
        # TODO: remove this print call
        print(str(response))
    print("_sendEvent done")

def sendEvent(name):
    if not isSendStatisticsAllowed():
        return
    instanceId = reggataInstanceId()
    if hlp.is_none_or_empty(instanceId):
        return
    t = Thread(target=_sendEvent, args=(instanceId, name))
    t.start()

