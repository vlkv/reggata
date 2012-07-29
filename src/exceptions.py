# -*- coding: utf-8 -*-
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

Created on 17.10.2010

@author: vlkv
'''

class LoginError(Exception):
    def __init__(self, msg=None):
        super(LoginError, self).__init__(msg)
        
class AccessError(Exception):
    def __init__(self, msg=None):
        super(AccessError, self).__init__(msg)
              
class UnsupportedDialogModeError(Exception):
    def __init__(self, msg=None):
        super(LoginError, self).__init__(msg)
        
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

class WrongValueError(Exception):
    def __init__(self, msg=None, cause=None):
        super(WrongValueError, self).__init__(msg)
        self.cause = cause
        
        