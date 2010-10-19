# -*- coding: utf-8 -*-
'''
Created on 16.10.2010

@author: vlkv
'''
from pyjavaproperties import Properties
import consts
import os

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
                os.mknod(consts.USER_CONFIG_FILE)
                
            #Если файла не существует, из load() вылетает исключение
            cls._props.load(open(consts.USER_CONFIG_FILE))
            
        return cls._instance
    
    def __init__(self):
        pass
    
    def get(self, key):
        return self._props[key]
    
    def store(self, key, value):
        self._props[key] = value
        self._props.store(open(consts.USER_CONFIG_FILE, 'w'))
        
    def storeAll(self, d):
        if type(d) != dict:
            raise TypeError("Тип аргумента d должен быть dict")
        for key in d.keys():
            self._props[key] = d[key]
        self._props.store(open(consts.USER_CONFIG_FILE, 'w'))
    
    def refresh(self):
        self._props.load(open(consts.USER_CONFIG_FILE))
        
#Это тестовый код
if __name__ == "__main__":
    uc1 = UserConfig()
    uc2 = UserConfig()
    print(uc1 == uc2)
    
    
    