# -*- coding: utf-8 -*-
'''
Created on 16.10.2010
@author: vlkv
'''
import os
import codecs
from reggata.pyjavaproperties import Properties
import reggata.reggata_default_conf as reggata_default_conf 
import reggata.consts as consts


class UserConfig(object):
    '''
        This class is an interface for reggata.conf configuration file.
    It is a singleton class.
    '''
    _instance = None
    _props = None
    
    def __new__(cls, *args, **kwargs):        
        if not cls._instance:            
            cls._instance = super(UserConfig, cls).__new__(cls, *args, **kwargs)
            
            cls._props = Properties()
            if not os.path.exists(consts.USER_CONFIG_DIR):
                os.makedirs(consts.USER_CONFIG_DIR)            
                
            if not os.path.exists(consts.USER_CONFIG_FILE):
                f = codecs.open(consts.USER_CONFIG_FILE, "w", "utf-8")
                try:
                    f.write(reggata_default_conf.reggataDefaultConf)
                finally:
                    f.close()
            
            cls._props.load(codecs.open(consts.USER_CONFIG_FILE, "r", "utf-8"))
        return cls._instance
    
    
    def __init__(self):
        pass
    
    
    def __getitem__(self, key):
        '''
            This is an operation []. It returns a value of parameter with given key.
        If there is no such key, an exception is raised.
        '''
        return self._props[key]
    
    def get(self, key, default=None):
        '''
            Returns value of parameter with given key. If there are no such key in
        configuration, then a default value is returned.
        '''
        return self._props.get(key, default)
    
    def store(self, key, value):
        self._props[key] = str(value)
        self._props.store(codecs.open(consts.USER_CONFIG_FILE, 'w', "utf-8"))
        
        
    def storeAll(self, d):
        if type(d) != dict:
            raise TypeError("This is not a dict instance.")
        for key in d.keys():
            self._props[key] = str(d[key])
        self._props.store(codecs.open(consts.USER_CONFIG_FILE, 'w', "utf-8"))
    
    def refresh(self):
        self._props.load(codecs.open(consts.USER_CONFIG_FILE, "r", "utf-8"))
        


if __name__ == "__main__":
    uc1 = UserConfig()
    uc2 = UserConfig()
    print(uc1 == uc2)
    print(uc1 is uc2)
    
    
    
    
    