# -*- coding: utf-8 -*-
'''
Created on 17.10.2010
@author: vlkv
'''

class NoneError(Exception):
    def __init__(self, msg=None):
        super(NoneError, self).__init__(msg)

class LoginError(Exception):
    def __init__(self, msg=None):
        super(LoginError, self).__init__(msg)
        
class AccessError(Exception):
    def __init__(self, msg=None):
        super(AccessError, self).__init__(msg)
              
class UnsupportedDialogModeError(Exception):
    def __init__(self, msg=None):
        super(UnsupportedDialogModeError, self).__init__(msg)
        
class MsgException(Exception):
    '''This exception is used in situations when no error occurred,
    but we have to tell the user some text information.'''
    def __init__(self, msg=None):
        super(MsgException, self).__init__(msg)
        
class CancelOperationError(Exception):
    def __init__(self):
        super(CancelOperationError, self).__init__()
        
class FileAlreadyExistsError(Exception):
    def __init__(self, msg=None):
        super(FileAlreadyExistsError, self).__init__(msg)

class DataRefAlreadyExistsError(Exception):
    def __init__(self, msg=None, cause=None):
        super(DataRefAlreadyExistsError, self).__init__(msg)
        self.cause = cause
        
class CannotOpenRepoError(Exception):
    def __init__(self, msg=None, cause=None):
        super(CannotOpenRepoError, self).__init__(msg)
        self.cause = cause
        
class CurrentRepoIsNoneError(Exception):
    def __init__(self, msg=None, cause=None):
        super(CurrentRepoIsNoneError, self).__init__(msg)
        self.cause = cause
        
class CurrentUserIsNoneError(Exception):
    def __init__(self, msg=None, cause=None):
        super(CurrentUserIsNoneError, self).__init__(msg)
        self.cause = cause

class LexError(Exception):
    def __init__(self, msg=None, cause=None):
        super(LexError, self).__init__(msg)
        self.cause = cause

class YaccError(Exception):
    def __init__(self, msg=None, cause=None):
        super(YaccError, self).__init__(msg)
        self.cause = cause
        
class NotFoundError(Exception):
    def __init__(self, msg=None, cause=None):
        super(NotFoundError, self).__init__(msg)
        self.cause = cause
        
class NotExistError(Exception):
    def __init__(self, msg=None, cause=None):
        super(NotExistError, self).__init__(msg)
        self.cause = cause

class WrongValueError(ValueError):
    def __init__(self, msg=None, cause=None):
        super(WrongValueError, self).__init__(msg)
        self.cause = cause
        
        