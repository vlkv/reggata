# -*- coding: utf-8 -*-
'''
Created on 30.09.2010

@author: vlkv
'''
from bsddb.test.test_all import path

class RepoMgr(object):
    '''
    Менеджер управления хранилищем в целом.
    '''

    '''Абсолютный путь к корню хранилища.'''
    __base_path = None

    def __init__(path_to_repo):
        '''
        Открывает хранилище по адресу path_to_repo. 
        Делает некторые проверки того, что хранилище корректно.
        '''
        pass
    
    @staticmethod
    def init_new_repo(base_path):
        '''
        Создаёт новое пустое хранилище по адресу base_path.
        '''
        pass
        