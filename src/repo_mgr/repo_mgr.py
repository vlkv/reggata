# -*- coding: utf-8 -*-
'''
Created on 30.09.2010

@author: vlkv
'''

import os.path
import sqlite3

class RepoMgr(object):
    '''Менеджер управления хранилищем в целом.'''

    '''Абсолютный путь к корню хранилища.'''
    __base_path = None

    def __init__(path_to_repo):
        '''Открывает хранилище по адресу path_to_repo. 
        Делает некторые проверки того, что хранилище корректно.'''
        pass
    
    @staticmethod
    def init_new_repo(base_path):
        '''Создаёт новое пустое хранилище по адресу base_path.
        1) Проверяет, что директория base_path существует
        2) Внутри base_path нет служебной поддиректории .reggata
        3) Создает служебную директорию .reggata и пустую sqlite базу внутри нее
        4) Создает объект RepoMgr, связывает его с созданным хранилищем и возвращает его
        '''
        if (not os.path.exists(base_path)):
            raise Exception('Необходимо сначала создать директорию ' + base_path)
        
        if (os.path.exists(base_path + os.sep + '.reggata')):
            raise Exception('Директория ' + base_path + ' уже является хранилищем?')
        
        os.mkdir(base_path + os.sep + '.reggata')
        
        conn = sqlite3.connect(base_path + os.sep + '.reggata' + os.sep + 'metadata.db3')
        try:
            c = conn.cursor()
            f = open('./init_repo.sql')
            lines = f.read().split(';')
            for line in lines:
                c.execute(line)
            conn.commit()
            c.close()
        finally:
            conn.close()
        
        #TODO Вернуть объект RepoMgr
        
        
    def check_integrity(self, path):
        '''Выполняет проверку целостности хранилища в поддиректории хранилища path.
        Что должен возвращать данный метод?
        '''
        pass
    
        