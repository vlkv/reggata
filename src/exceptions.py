# -*- coding: utf-8 -*-
'''
Created on 17.10.2010

@author: vlkv
'''

class LoginError(Exception):
    def __init__(self, msg):
        super(LoginError, self).__init__(msg)
        
class AccessError(Exception):
    def __init__(self, msg):
        super(AccessError, self).__init__(msg)
        
class UnsupportedDialogModeError(Exception):
    def __init__(self, msg):
        super(LoginError, self).__init__(msg)
        
class MsgException(Exception):
    '''Исключение для тех случаев, когда ошибок нет, но нужно отобразить
    пользователю какую-нибудь информацию.'''
    def __init__(self, msg):
        super(MsgException, self).__init__(msg)