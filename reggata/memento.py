'''
Created on 27.07.2012
@author: vlkv
'''
import sys
import json
import datetime


class Serializable(object):
    def toJson(self):
        raise NotImplementedError()

    @staticmethod
    def fromJson(objState):
        raise NotImplementedError()


class Encoder(json.JSONEncoder):
    def __init__(self, indent=4, sort_keys=True):
        json.JSONEncoder.__init__(self, indent=indent, sort_keys=sort_keys)

    def default(self, obj):
        if isinstance(obj, Serializable):
            return obj.toJson()
        if isinstance(obj, datetime.datetime):
            return {"__datetime__": obj.__repr__()}
        else:
            return json.JSONEncoder.default(self, obj)


def Decoder():
    return json.JSONDecoder(object_hook=hook)


def hook(objState):
    if "__class__" in objState and "__module__" in objState:
        __import__(objState["__module__"])
        cls = getattr(sys.modules[objState["__module__"]], objState["__class__"])
        return cls.fromJson(objState)

    elif "__datetime__" in objState:
        return eval(objState["__datetime__"])

    else:
        return objState
