# -*- coding: utf-8 -*-
'''
Created on 30.09.2010

@author: vlkv
'''

import os.path
import sqlite3
from consts import  *
from translator_helper import tr

class RepoMgr(object):
    '''Менеджер управления хранилищем в целом.'''

    '''Абсолютный путь к корню хранилища '''
    __base_path = None
    
    '''Соединение с базой метаданных '''
    __conn = None

    def __init__(self, path_to_repo):
        '''Открывает хранилище по адресу path_to_repo. 
        Делает некторые проверки того, что хранилище корректно.'''
        self.__base_path = path_to_repo
        if not os.path.exists(self.__base_path + os.sep + METADATA_DIR):
            raise Exception(tr("Директория " + self.__base_path + " не является хранилищем."))
        
        __conn = sqlite3.connect(self.__base_path + os.sep + METADATA_DIR + os.sep + DB_FILE)
        
    def __del__(self):
        if self.__conn is not None:
            self.__conn.close()
    
    @staticmethod
    def init_new_repo(base_path):
        '''Создаёт новое пустое хранилище по адресу base_path.
        1) Проверяет, что директория base_path существует
        2) Внутри base_path нет служебной поддиректории .reggata
        3) Создает служебную директорию .reggata и пустую sqlite базу внутри нее
        '''
        if (not os.path.exists(base_path)):
            raise Exception(tr('Необходимо сначала создать директорию ') + base_path)
        
        if (os.path.exists(base_path + os.sep + METADATA_DIR)):
            raise Exception(tr('Директория ') + base_path + tr(' уже является хранилищем?'))
        
        os.mkdir(base_path + os.sep + METADATA_DIR)
        
        conn = sqlite3.connect(base_path + os.sep + METADATA_DIR + os.sep + DB_FILE)
        try:
            c = conn.cursor()
            f = open(INIT_DB_SQL)
            lines = f.read().split(';')
            for line in lines:
                c.execute(line)
            conn.commit()
            c.close()
        finally:
            conn.close()
        
    @staticmethod
    def create_new_repo(base_path):
        RepoMgr.init_new_repo(base_path)
        return RepoMgr(base_path)
        
        
    def check_integrity(self, path):
        '''Выполняет проверку целостности хранилища в поддиректории хранилища path.
        Что должен возвращать данный метод?
        '''
        #TODO
        pass
    
        