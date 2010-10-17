# -*- coding: utf-8 -*-
'''
Created on 30.09.2010

@author: vlkv
'''

import os.path
from helpers import tr
import consts
import sqlalchemy as sqa
from sqlalchemy.orm import sessionmaker
from db_model import Base, Item, User
from exceptions import LoginError

class RepoMgr(object):
    '''Менеджер управления хранилищем в целом.'''
    
    '''Соединение с базой метаданных '''
    __engine = None
    
    '''Класс сессии '''
    Session = None
    
    _base_path = None

    def __init__(self, path_to_repo):
        '''Открывает хранилище по адресу path_to_repo. 
        Делает некторые проверки того, что хранилище корректно.'''
        self.base_path = path_to_repo
        if not os.path.exists(self.base_path + os.sep + consts.METADATA_DIR):
            raise Exception(tr("Директория " + self.base_path + " не является хранилищем."))
        
        self.__engine = sqa.create_engine("sqlite:///" + self.base_path + os.sep + consts.METADATA_DIR + os.sep + consts.DB_FILE)

        self.Session = sessionmaker(bind=self.__engine) #expire_on_commit=False
        
    def __del__(self):
        pass
    
    @property
    def base_path(self):
        '''Абсолютный путь к корню хранилища.'''
        return self._base_path
    
    @base_path.setter
    def base_path(self, value):
        self._base_path = value
            
    
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

    def createUnitOfWork(self):
        return UnitOfWork(self)


class UnitOfWork(object):
    
    __session = None

    def __init__(self, repoMgr):
        self.__session = repoMgr.Session()    
        
    def __del__(self):
        if self.__session is not None:
            self.__session.close()
        
    def close(self):
        self.__session.expunge_all()
        self.__session.close()
        
    def saveNewUser(self, user):
#        login = user.login
        self.__session.add(user)
        self.__session.commit()
#        user = self.__session.query(User).get(login)

    def loginUser(self, login, password):
        user = self.__session.query(User).get(login)
        if user is None:
            raise LoginError(tr("Пользователя ") + login + tr(" не существует."))
        if user.password != password:
            raise LoginError(tr("Неверный пароль"))
        return user
        
            
        

        
    def saveNewItem(self, item):
        self.__session.add(item)
        self.__session.commit()
        
        


