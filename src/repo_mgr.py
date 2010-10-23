# -*- coding: utf-8 -*-
'''
Created on 30.09.2010

@author: vlkv
'''

import os.path
from helpers import tr, to_commalist
import consts
import sqlalchemy as sqa
from sqlalchemy.orm import sessionmaker
from db_model import Base, Item, User, Tag, Field
from exceptions import LoginError
import shutil

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
    
    _repo_base_path = None
    
    _session = None
    
    def __init__(self, repoMgr):
        self._repo_base_path = repoMgr.base_path
        self._session = repoMgr.Session()
        
    def __del__(self):
        if self._session is not None:
            self._session.close()
        
    def close(self):
        self._session.expunge_all()
        self._session.close()
        
    #TODO Надо подумать про rollback()...
        
    def getTags(self, user_logins=[]):
        '''Возвращает список тегов хранилища.'''
        if len(user_logins) == 0:
            return self._session.query(Tag).order_by(Tag.name).all()
        else:
            return self._session.query(Tag) \
                    .filter(Tag.user_login.in_(user_logins)) \
                    .order_by(Tag.name).all()
        #TODO нужны критерии по пользователям и по уже выбранным тегам
        
    
    def queryItems(self, and_tags):
#        return self._session.query(Item).filter(Item.tags.any(Tag.name.in_(and_tags))).all()
        sql = '''SELECT DISTINCT i.id, i.title, i.notes, i.user_login
                    FROM items i LEFT JOIN tags_items ti on i.id=ti.item_id 
                    WHERE ti.tag_name IN (''' + to_commalist(and_tags) + ''')'''
        print(sql)
        return self._session.query(Item).from_statement(sql).all()
    
    def saveNewUser(self, user):
        self._session.add(user)
        self._session.commit()


    def loginUser(self, login, password):
        '''
    	password - это SHA1 hexdigest() хеш.
    	'''
        user = self._session.query(User).get(login)
        if user is None:
            raise LoginError(tr("Пользователя ") + login + tr(" не существует."))
        if user.password != password:
            raise LoginError(tr("Неверный пароль"))
        return user

        
    def saveNewItem(self, item):
            
        copy_list = []
        
        #Сначала надо преобразовать пути у объектов DataRef
        for dr in item.data_refs:
            
            #Нормализация пути
            dr.url = os.path.normpath(dr.url)
            
            #Убираем слеш, если есть в конце пути
            if dr.url.endswith(os.sep):
                dr.url = dr.url[0:len(dr.url)-1]
            
            #Запоминаем на время
            tmp_url = dr.url
        
            #Определяем, находится ли данный файл уже внутри хранилища
            com_pref = os.path.commonprefix([self._repo_base_path, dr.url])
            if com_pref == self._repo_base_path:
                #Файл уже внутри
                #Нужно сделать путь dr.url относительным и всё
                dr.url = os.path.relpath(dr.url, self._repo_base_path)
            else:
                #Файл снаружи
                #Такой файл будет скопирован в корень хранилища
                dr.url = os.path.basename(dr.url)
            
            #Запоминаем все пути к файлам из DataRef объектов, чтобы потом копировать
            copy_list.append((tmp_url, dr.url))
        
        #Удаляем из item.tags теги, которые уже есть в базе
        tags = item.tags[:] #Делаем копию списка
        new_tags = []
        for tag in tags:
            t = self._session.query(Tag).get((tag.name, tag.user_login))
            if t is not None:                
                new_tags.append(t)
                item.tags.remove(tag) #Оставляем в item.tags только новые теги            
        
        #Удаляем поля, которые уже существуют
        field_vals = item.field_vals[:]
        new_field_vals = []
        for field_val in field_vals:
            field = field_val.field
            f = self._session.query(Field).get((field.name, field.user_login))
            if f is not None:
                field_val.field = f
                new_field_vals.append(field_val)
                item.field_vals.remove(field_val)
                

        #Сохраняем item пока что только с новыми тегами и новыми полями
        self._session.add(item)
        self._session.flush()
        
        #Добавляем в item существующие теги
        for tag in new_tags:
            item.tags.append(tag)
        
        #Добавляем в item существующие поля
        for field_val in new_field_vals:
            item.field_vals.append(field_val)
                        
        self._session.commit()
        
        #Если все сохранилось в БД, то копируем файлы
        for dr in copy_list:
            if dr[0] != self._repo_base_path + dr[1]:
                shutil.copy(dr[0], self._repo_base_path + dr[1])
        #TODO надо копировать не просто в корень...
        
        #TODO надо вычислять хеши



