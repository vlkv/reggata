# -*- coding: utf-8 -*-
'''
Created on 16.10.2010
@author: vlkv
'''

import consts
import os
import codecs
from pyjavaproperties import Properties
import reggata_default_conf


class UserConfig(object):
    '''
    Класс для упрощения доступа к содержимому конфиг-файла в домашней директории пользователя.
    Этот класс реализован по паттерну одиночка (singleton pattern).
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
        '''Операция [], возвращает значение параметра с ключом key. Если ключ key не существует, то выкидывается исключение.'''
        return self._props[key]
    
    def get(self, key, default=None):
        '''Возвращает значение параметра с ключом key. Если ключа key не существует, то
        возвращает значение аргумента default. Если default не задан, то его значение по 
        умолчанию равно None.'''
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
    
    
    
    
    