# -*- coding: utf-8 -*-
'''
Created on 30.09.2010

@author: vlkv
'''

import os.path
from translator_helper import tr
import consts
import sqlalchemy as sqa
from sqlalchemy.orm import sessionmaker
from db_model import Base, Item

class RepoMgr(object):
    '''Менеджер управления хранилищем в целом.'''

    '''Абсолютный путь к корню хранилища '''
    __base_path = None
    
    '''Соединение с базой метаданных '''
    __engine = None
    
    '''Класс сессии '''
    Session = None

    def __init__(self, path_to_repo):
        '''Открывает хранилище по адресу path_to_repo. 
        Делает некторые проверки того, что хранилище корректно.'''
        self.__base_path = path_to_repo
        if not os.path.exists(self.__base_path + os.sep + consts.METADATA_DIR):
            raise Exception(tr("Директория " + self.__base_path + " не является хранилищем."))
        
        self.__engine = sqa.create_engine("sqlite:///" + self.__base_path + os.sep + consts.METADATA_DIR + os.sep + consts.DB_FILE)

        self.Session = sessionmaker(bind=self.__engine)
        
    def __del__(self):
        pass
    
    @staticmethod
    def init_new_repo(base_path):
        '''Создаёт новое пустое хранилище по адресу base_path.
        1) Проверяет, что директория base_path существует
        2) Внутри base_path нет служебной поддиректории .reggata
        3) Создает служебную директорию .reggata и пустую sqlite базу внутри нее
        '''
        if (not os.path.exists(base_path)):
            raise Exception(tr('Необходимо сначала создать директорию ') + base_path)
        
        if (os.path.exists(base_path + os.sep + consts.METADATA_DIR)):
            raise Exception(tr('Директория ') + base_path + tr(' уже является хранилищем?'))
        
        os.mkdir(base_path + os.sep + consts.METADATA_DIR)
        
        #Соединение с БД
        engine = sqa.create_engine("sqlite:///" + base_path + os.sep + consts.METADATA_DIR + os.sep + consts.DB_FILE)
         
        #Создание таблиц в БД
        Base.metadata.create_all(engine)
        
        
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

    def createItemMgr(self):
        itemMgr = ItemMgr(self)
        return itemMgr


class ItemMgr(object):
    
    __session = None

    def __init__(self, repoMgr):
        self.__session = repoMgr.Session()    
        
    def __del__(self):
        self.close()
        
    def close(self):
        self.__session.close()
        
    def addTestItem(self, title):
#        self.__session.begin()
        item = Item()
        item.title = title
        item.notes = "bla-bla-bla"
        self.__session.add(item)
        self.__session.commit()
    
