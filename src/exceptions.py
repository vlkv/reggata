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
        
class FileAlreadyExistsError(Exception):
    def __init__(self, msg):
        super(FileAlreadyExistsError, self).__init__(msg)
        
        
        
        
        