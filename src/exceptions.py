'''
Created on 17.10.2010

@author: vlkv
'''

class LoginError(Exception):
    def __init__(self, msg):
        super(LoginError, self).__init__(msg)
        
class UnsupportedDialogModeError(Exception):
    def __init__(self, msg):
        super(LoginError, self).__init__(msg)
        