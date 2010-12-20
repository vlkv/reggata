# -*- coding: utf-8 -*-
'''
Copyright 2010 Vitaly Volkov

This file is part of Reggata.

Reggata is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Reggata is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Reggata.  If not, see <http://www.gnu.org/licenses/>.

Created on 30.09.2010

@author: vlkv
'''

import os.path
from helpers import tr, to_commalist, is_none_or_empty, index_of, is_internal,\
    compute_hash
import consts
import sqlalchemy as sqa
from sqlalchemy.orm import sessionmaker, joinedload, contains_eager,\
    joinedload_all
from db_schema import Base, Item, User, Tag, Field, Item_Tag, DataRef, Item_Field,\
    Thumbnail, HistoryRec
from exceptions import LoginError, AccessError, FileAlreadyExistsError,\
    CannotOpenRepoError, NotFoundError, WrongValueError
import shutil
import PyQt4.QtGui as QtGui
import PyQt4.QtCore as QtCore
import datetime
from sqlalchemy.exc import ResourceClosedError
from sqlalchemy.sql.expression import select
from user_config import UserConfig
import db_schema
import traceback
import os
import helpers
import sys
from integrity_fixer import IntegrityFixer


class RepoMgr(object):
    '''Менеджер управления хранилищем в целом.'''
        
    def __init__(self, path_to_repo):
        '''Открывает хранилище по адресу path_to_repo. 
        Делает некторые проверки того, что хранилище корректно.'''
        
        try:
            #self._base_path --- Абсолютный путь к корню хранилища
            self._base_path = path_to_repo
            if not os.path.exists(self.base_path + os.sep + consts.METADATA_DIR):
                raise Exception(tr("Directory {} is not a repository base path.").format(self.base_path))
            
            engine_echo = bool(UserConfig().get("sqlalchemy.engine_echo") in ["True", "true", "TRUE", "1", "Yes", "yes", "YES"]) 
            
            #self.__engine --- Соединение с базой метаданных
            self.__engine = sqa.create_engine(\
                "sqlite:///" + self.base_path + os.sep + consts.METADATA_DIR + os.sep + consts.DB_FILE, \
                echo=engine_echo)
            
            
            #Класс сессии
            self.Session = sessionmaker(bind=self.__engine) #expire_on_commit=False
        except Exception as ex:
            raise CannotOpenRepoError(ex)
        
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
            raise Exception(tr("Directory {} doesn't exists.").format(base_path))
        
        if (os.path.exists(base_path + os.sep + consts.METADATA_DIR)):
            raise Exception(tr("It looks like {} is already a repository base path.").format(base_path))
        
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
        raise NotImplementedError()

    def create_unit_of_work(self):
        return UnitOfWork(self)


class UnitOfWork(object):
    
    def __init__(self, repoMgr):
        self._repo_base_path = repoMgr.base_path
        self._session = repoMgr.Session()        
        
    def __del__(self):
        if self._session is not None:
            self._session.close()
        
    def close(self):
        self._session.expunge_all()
        self._session.close()
        
    @property
    def session(self):
        return self._session
        
        
    def save_thumbnail(self, data_ref_id, thumbnail):
        data_ref = self._session.query(DataRef).get(data_ref_id)
        
        self._session.add(thumbnail)
        self._session.flush()
        
        data_ref.thumbnails.append(thumbnail)
        self._session.commit()
        
        self._session.refresh(thumbnail)
        self._session.expunge(thumbnail)
        self._session.expunge(data_ref)
        
        
        
    def get_related_tags(self, tag_names=[], user_logins=[]):
        ''' Возвращает список related тегов для тегов из списка tag_names.
        Если tag_names - пустой список, возращает все теги.
        Поиск ведется среди тегов пользователей из списка user_logins.
        Если user_logins пустой, то поиск среди всех тегов в БД.
        '''
        
        #TODO Пока что не учитывается аргумент user_logins
        
        if len(tag_names) == 0:
            sql = '''
            --get_related_tags() запрос, извлекающий все теги и кол-во связанных с каждым тегом ЖИВЫХ элементов
            select t.name as name, count(*) as c
               from items i, tags t
               join items_tags it on it.tag_id = t.id and it.item_id = i.id and i.alive   
            where
                1
            group by t.name
            ORDER BY t.name
            '''
            
            #Здесь пришлось вставлять этот try..except, т.к. иначе пустой список (если нет связанных тегов)
            #не возвращается, а вылетает ResourceClosedError. Не очень удобно, однако. 
            try:
                return self._session.query("name", "c").from_statement(sql).all()
            except ResourceClosedError as ex:
                return []
            
            
        else:                
            #Сначала нужно получить список id-шников для всех имен тегов
            sql = '''--get_related_tags(): getting list of id for all selected tags
            select * from tags t
            where t.name in (''' + to_commalist(tag_names, lambda x: "'" + x + "'") + ''')
            order by t.id'''
            tags = self._session.query(Tag).from_statement(sql).all()
            tag_ids = []
            for tag in tags:
                tag_ids.append(tag.id)
            
            sub_from = ""
            for i in range(len(tag_ids)):
                if i == 0:
                    sub_from = sub_from + " items_tags it{} ".format(i+1)
                else:
                    sub_from = sub_from + \
                    (" join items_tags it{1} on it{1}.item_id=it{0}.item_id " + \
                    " AND it{1}.tag_id > it{0}.tag_id ").format(i, i+1)
                
            sub_where = ""
            for i in range(len(tag_ids)):
                if i == 0:
                    sub_where = sub_where + \
                    " it{0}.tag_id = {1} ".format(i+1, tag_ids[i])
                else:
                    sub_where = sub_where + \
                    " AND it{0}.tag_id = {1} ".format(i+1, tag_ids[i])
            
            where = ""
            for i in range(len(tag_ids)):
                where = where + \
                " AND t.id <> {0} ".format(tag_ids[i])
            
            sql = '''--get_related_tags() запрос, извлекающий родственные теги для выбранных тегов
            select t.name as name, count(*) as c
                from tags t
                join items_tags it on it.tag_id = t.id
                join items i on i.id = it.item_id
            where
                it.item_id IN (
                    select it1.item_id
                        from ''' + sub_from + '''
                    where ''' + sub_where + '''                     
                ) ''' + where + '''
                AND i.alive            
                --Важно, чтобы эти id-шники следовали по возрастанию                
            group by t.name
            ORDER BY t.name'''
            try:            
                return self._session.query("name", "c").from_statement(sql).all()
            except ResourceClosedError as ex:
                return []
    
    def get_item(self, id):
        '''Возвращает detached-объект класса Item, с заданным значением id. '''
        item = self._session.query(Item)\
            .options(joinedload_all('data_ref'))\
            .options(joinedload_all('item_tags.tag'))\
            .options(joinedload_all('item_fields.field'))\
            .get(id)
        self._session.expunge(item)
        return item
    
    def get_untagged_items(self):
        '''
        Извлекает из БД все ЖИВЫЕ элементы, с которыми не связано ни одного тега.
        '''
        
        thumbnail_default_size = UserConfig().get("thumbnail_size", consts.THUMBNAIL_DEFAULT_SIZE)
        
        sql = '''--Извлекает все элементы, с которыми не связано ни одного тега
        select sub.*, ''' + \
        Item_Tag._sql_from() + ", " + \
        Tag._sql_from() + ", " + \
        Item_Field._sql_from() + ", " + \
        Field._sql_from() + \
        '''
        from (select i.*, ''' + \
            DataRef._sql_from() + ", " + \
            Thumbnail._sql_from() + \
            ''' 
            from items i
            left join items_tags it on i.id = it.item_id
            left join data_refs on i.data_ref_id = data_refs.id
            left join thumbnails on data_refs.id = thumbnails.data_ref_id and thumbnails.size = {} 
            where 
                it.item_id is null
                AND i.alive 
        ) as sub
        left join items_tags on sub.id = items_tags.item_id
        left join tags on tags.id = items_tags.tag_id
        left join items_fields on sub.id = items_fields.item_id
        left join fields on fields.id = items_fields.field_id 
        '''.format(thumbnail_default_size)
                
        items = []
        try:
            items = self._session.query(Item)\
            .options(contains_eager("data_ref"), \
                     contains_eager("data_ref.thumbnails"), \
                     contains_eager("item_tags"), \
                     contains_eager("item_tags.tag"), \
                     contains_eager("item_fields"),\
                     contains_eager("item_fields.field"))\
            .from_statement(sql).all()
            for item in items:
                self._session.expunge(item)
                            
        except ResourceClosedError:
                pass
                
        return items
    
    def query_items_by_tree(self, query_tree):
        '''
        Функция извлекает item-ы, которые соответствуют дереву разбора query_tree.
        '''
        
        sub_sql = query_tree.interpret()
        
        sql = '''
        select sub.*, 
        ''' + db_schema.Item_Tag._sql_from() + ''', 
        ''' + db_schema.Tag._sql_from() + ''',
        ''' + db_schema.Thumbnail._sql_from() + ''',
        ''' + db_schema.Item_Field._sql_from() + ''',
        ''' + db_schema.Field._sql_from() + '''        
        from (''' + sub_sql + ''') as sub
        left join items_tags on sub.id = items_tags.item_id
        left join tags on tags.id = items_tags.tag_id
        left join items_fields on sub.id = items_fields.item_id
        left join fields on fields.id = items_fields.field_id
        left join thumbnails on thumbnails.data_ref_id = sub.data_refs_id and 
                  thumbnails.size = ''' + str(UserConfig().get("thumbnail_size", consts.THUMBNAIL_DEFAULT_SIZE)) + '''
        where sub.alive
        '''
        
        items = []
        try:
            items = self._session.query(Item)\
            .options(contains_eager("data_ref"), \
                     contains_eager("data_ref.thumbnails"), \
                     contains_eager("item_tags"), \
                     contains_eager("item_tags.tag"), \
                     contains_eager("item_fields"),\
                     contains_eager("item_fields.field"))\
            .from_statement(sql).all()
    
            for item in items:
                self._session.expunge(item)
        
        except ResourceClosedError:
                pass
                
        return items
        
    
#    def query_items_by_sql(self, sql):
#        '''
#        Внимание! sql должен извлекать не только item-ы, но также и связанные (при помощи left join)
#        элементы data_refs и thumbnails.
#        '''
#        
##Это так для примера: как я задавал alias
##        data_refs = Base.metadata.tables[DataRef.__tablename__]
##        thumbnails = Base.metadata.tables[Thumbnail.__tablename__]        
##        eager_columns = select([
##                    data_refs.c.id.label('dr_id'),
##                    data_refs.c.url.label('dr_url'),
##                    data_refs.c.type.label('dr_type'),
##                    data_refs.c.hash.label('dr_hash'),
##                    data_refs.c.date_hashed.label('dr_date_hashed'),
##                    data_refs.c.size.label('dr_size'),
##                    data_refs.c.date_created.label('dr_date_created'),
##                    data_refs.c.user_login.label('dr_user_login'),
##                    thumbnails.c.data_ref_id.label('th_data_ref_id'),
##                    thumbnails.c.size.label('th_size'),
##                    thumbnails.c.dimension.label('th_dimension'),
##                    thumbnails.c.data.label('th_data'),
##                    thumbnails.c.date_created.label('th_date_created'),
##                    ])                    
##        items = self._session.query(Item).\
##            options(contains_eager("data_ref", alias=eager_columns), \                    
##                    contains_eager("data_ref.thumbnails", alias=eager_columns)).\
##            from_statement(sql).all()
#
#        items = self._session.query(Item)\
#            .options(contains_eager("data_ref"), \
#                     contains_eager("data_ref.thumbnails"), \
#                     contains_eager("item_tags"), \
#                     contains_eager("item_tags.tag"))\
#            .from_statement(sql).all()
#            
#        #Выше использовался joinedload, поэтому по идее следующий цикл
#        #не должен порождать новые SQL запросы
##        for item in items:
##            item.data_ref
##            for thumbnail in item.data_ref.thumbnails:
##                thumbnail
#
#        for item in items:
#            self._session.expunge(item)
#        
#        return items
#    
    
    
    def save_new_user(self, user):
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)
        self._session.expunge(user)


    def login_user(self, login, password):
        '''
    	password - это SHA1 hexdigest() хеш. В случае неверного логина или пароля, 
    	выкидывается LoginError.
    	'''
        if is_none_or_empty(login):
            raise LoginError(tr("User login cannot be empty."))
        user = self._session.query(User).get(login)
        if user is None:
            raise LoginError(tr("User {} doesn't exist.").format(login))
        if user.password != password:
            raise LoginError(tr("Password incorrect."))
        
        self._session.expunge(user)
        return user

    @staticmethod
    def _check_item_integrity(session, item, repo_base_path):
        '''Возвращает множество целых чисел (кодов ошибок). Коды ошибок (константы)
        объявлены как статические члены класса Item.
        
        Если ошибок нет, то возвращает пустое множество.
        '''
        
        error_set = set()
        
        #Нужно проверить, есть ли запись в истории
        hr = UnitOfWork._find_item_latest_history_rec(session, item)
        if hr is None:
            error_set.add(Item.ERROR_HISTORY_REC_NOT_FOUND)
        
        #Если есть связанный DataRef объект типа FILE,
        if item.data_ref is not None and item.data_ref.type == DataRef.FILE:                    
            #    нужно проверить есть ли файл
            abs_path = os.path.join(repo_base_path, item.data_ref.url)
            if not os.path.exists(abs_path):
                error_set.add(Item.ERROR_FILE_NOT_FOUND)
            else:                                            
                #    нужно проверить, совпадает ли хеш файла со значением DataRef.hash
                hash = helpers.compute_hash(abs_path)
                if item.data_ref.hash != hash:
                    error_set.add(Item.ERROR_FILE_HASH_MISMATCH)
                
                #    можно проверить, если size не совпадает, то hash тоже совпадать не должен будет
                size = os.path.getsize(abs_path)
                if item.data_ref.size != size:
                    error_set.add(Item.ERROR_FILE_SIZE_MISMATCH)
        
        return error_set

    @staticmethod
    def _find_item_latest_history_rec(session, item_0):
        '''
        Возвращает последнюю запись из истории, относящуюся к элементу item_0.
        Либо возвращает None, если не удалось найти такую запись.
        '''
        data_ref_hash = None
        data_ref_url = None
        if item_0.data_ref is not None:
            data_ref_hash = item_0.data_ref.hash
            data_ref_url = item_0.data_ref.url
        parent_hr = session.query(HistoryRec).filter(HistoryRec.item_id==item_0.id)\
                .filter(HistoryRec.item_hash==item_0.hash())\
                .filter(HistoryRec.data_ref_hash==data_ref_hash)\
                .filter(HistoryRec.data_ref_url==data_ref_url)\
                .order_by(HistoryRec.id.desc()).first()
        return parent_hr
    
    @staticmethod
    def _save_history_rec(session, item_0, user_login, operation, parent1_id=None, parent2_id=None):
        
        if operation is None:
            raise ValueError(tr("Argument operation cannot be None."))
        
        if operation != HistoryRec.CREATE and parent1_id is None:
            raise ValueError(tr("Argument parent1_id cannot be None in CREATE operation."))
        
        #Сохраняем историю изменения данного элемента
        hr = HistoryRec(item_id = item_0.id, item_hash=item_0.hash(), \
                        operation=operation, \
                        user_login=user_login, \
                        parent1_id = parent1_id, parent2_id = parent2_id)
        if item_0.data_ref is not None:
            hr.data_ref_hash = item_0.data_ref.hash
            hr.data_ref_url = item_0.data_ref.url
        session.add(hr)
        
        
    def update_existing_item(self, item, user_login):
        '''Изменяет состояние существующего элемента хранилища. Поскольку в принципе, пользователь
        может добавлять свои теги к чужому элементу, то необходимо передавать логин
        пользователя, который осуществляет редактирование (т.е. user_login).
        
        То, что у item.data_ref может быть изменен url, означает, что пользователь
        хочет привязать данный item к другому файлу (data_ref-объекту). При этом, 
        поле item.data_ref.dst_path определяет в какую поддиректорию хранилища будет
        СКОПИРОВАН привязываемый файл.
        
        Если у item.data_ref поле url не изменено, но имеется значение в поле 
        item.data_ref.dst_path, тогда это означает, что пользователь хочет
        ПЕРЕМЕСТИТЬ существующий (уже связанный с данным item-ом) файл в другую 
        поддиректорию хранилища (также нужна модификация соотв. data_ref-объекта).
        
        Передаваемый item должен быть в detached состоянии.
        '''
        #TODO Тут наверное нужно запрещать пользователю удалять чужие теги, поля и data_ref-ы!!!
        #Редактировать чужие item-ы
        
        #Ищем в БД элемент в его первоначальном состоянии
        #item_0 это объект, который будет принадлежать текущей сессии self._session
        item_0 = self._session.query(Item).get(item.id)
        
        #Нужно взять из истории запись, соответствующую состоянию объекта item_0
        parent_hr = UnitOfWork._find_item_latest_history_rec(self._session, item_0)
        if parent_hr is None:
            raise Exception(tr("HistoryRec for Item object id={0} not found.").format(item_0.id))
            #TODO Пользователю нужно сказать, чтобы он вызывал функцию проверки целостности и исправления ошибок
        
        #Редактирование полей, которые можно редактировать (вообще у item-а есть еще и другие поля).
        item_0.title = item.title
        item_0.notes = item.notes
        item_0.user_login = item.user_login
        self._session.flush()
        
                
        #Удаление тегов
        #Если в item_0 есть теги, которых нет в item, то их нужно удалить
        for itag in item_0.item_tags:
            i = index_of(item.item_tags, lambda x: True if x.tag.name==itag.tag.name else False)
            if i is None:
                #Помечаем для удаления соответствующий Item_Tag объект
                #Объект Tag остается в БД (даже если на него не останется ссылок)
                self._session.delete(itag)
        self._session.flush()
        
        #Добавление тегов
        #Если в item есть теги, которых нет в item_0, то их нужно создать
        for itag in item.item_tags:
            i = index_of(item_0.item_tags, lambda x: True if x.tag.name==itag.tag.name else False)
            if i is None:
                #Ищем в БД тег, который нужно добавить к item_0
                tag = self._session.query(Tag).filter(Tag.name==itag.tag.name).first()
                if tag is None:
                    #Такого тега нет, нужно сначала его создать
                    tag = Tag(itag.tag.name)
                    self._session.add(tag)
                    self._session.flush()
                #Теперь тег точно есть, просто привязываем его к item_0
                item_tag = Item_Tag(tag, user_login)
                self._session.add(item_tag)
                item_tag.item = item_0
                item_0.item_tags.append(item_tag) #Почему нужно обе стороны связывать? Ведь relation?
        self._session.flush()
                
        #Удаление полей (Ищем какие поля присутствуют в item_0 и отсутствуют в item)
        for ifield in item_0.item_fields:
            i = index_of(item.item_fields, lambda o: True if o.field.name==ifield.field.name else False)
            if i is None:
                self._session.delete(ifield)
        self._session.flush()
        
        #Добавление новых полей, либо изменение значений существующих
        #Ищем какие поля есть в item, которых нет в item_0 (либо есть в item_0, но имеют другое значение)
        for ifield in item.item_fields:
            i = index_of(item_0.item_fields, \
                         lambda o: True if o.field.name==ifield.field.name else False)
            if i is None:
                #К элементу нужно привязать новое поле
                #Ищем сначала в БД соответствующий объект Field
                field = self._session.query(Field).filter(Field.name==ifield.field.name).first()
                if field is None: 
                    #Такого поля нет, нужно создать
                    field = Field(ifield.field.name)
                    self._session.add(field)
                    self._session.flush()
                item_field = Item_Field(field, ifield.field_value, user_login)
                self._session.add(item_field)
                item_field.item = item_0
                item_0.item_fields.append(item_field)
            elif ifield.field_value != item_0.item_fields[i].field_value:
                #У элемента данное поле есть, но нужно изменить его значение
                self._session.add(item_0.item_fields[i]) #Вот тут не могу понять, почему этот объект Item_Field нужно явно добавлять в сессию?
                item_0.item_fields[i].field_value = ifield.field_value
        self._session.flush()
        
        
        #Проведение операций со связанным DataRef объектом (и физическим файлом)
        abs_src_path = None
        need_file_operation = None
        
        if item.data_ref is None:
            #У элемента удалили ссылку на на DataRef (либо она и раньше была пустой).
            #Сам DataRef объект и файл удалять не хочется... пока что так
            #TODO Сделать удаление, если на данный DataRef не ссылаются другие элементы
            item_0.data_ref = None
            item_0.data_ref_id = None
        elif item_0.data_ref is None or item_0.data_ref.url != item.data_ref.url:
            #Элемент привязывается к DataRef-у впервые либо перепривязывается к другому DataRef объекту.
            #Смотрим, может быть привязываемый файл уже внутри хранилища, и уже может быть есть даже объект DataRef?
            #Надо сделать адрес относительным, если тип DataRef-а равен FILE
            if item.data_ref.type == DataRef.FILE and item.data_ref.url.startswith(self._repo_base_path):
                url = os.path.relpath(item.data_ref.url, self._repo_base_path)
            else:
                url = item.data_ref.url
            existing_data_ref = self._session.query(DataRef).filter(DataRef.url==url).first()            
            if existing_data_ref is not None:
                item_0.data_ref = existing_data_ref
            else:
                #Объекта DataRef в БД не существует, нужно его создавать
                #Две ситуации: файл уже внутри хранилища, либо он снаружи
                #В любом случае item.data_ref.url содержит изначально абсолютный адрес (или URL-ссылку!)                                
                abs_src_path = item.data_ref.url
                self._prepare_data_ref(item.data_ref, user_login)
                self._session.add(item.data_ref)
                self._session.flush()
                item_0.data_ref = item.data_ref
                #Если был создан DataRef типа FILE, то файл потом нужно скопировать
                if item.data_ref.type == DataRef.FILE:
                    need_file_operation = "copy"
                
        elif item.data_ref.type == DataRef.FILE and not is_none_or_empty(item.data_ref.dst_path):
            #У элемента не меняется его привязка к DataRef объекту
            #Но, возможно, было задано поле data_ref.dst_path и data_ref нужно
            #ПЕРЕМЕСТИТЬ в другую директорию хранилища
            #dst_path в данном случае должен содержать относительный путь до директории назначения.
                        
            #Запоминаем исходное расположение файла
            abs_src_path = os.path.join(self._repo_base_path, item_0.data_ref.url)
            
            #Преобразуем dst_path в абсолютный путь ДО ФАЙЛА
            dst_path = os.path.join(item.data_ref.dst_path, os.path.basename(item.data_ref.url)) 
            abs_dst_path = os.path.join(self._repo_base_path, dst_path)
            
            if not os.path.exists(abs_src_path):
                raise Exception(tr("File {0} not found!").format(abs_src_path))
            if not os.path.exists(abs_dst_path):
                item_0.data_ref.url = dst_path
                need_file_operation = "move"
            elif os.path.abspath(abs_src_path) != os.path.abspath(abs_dst_path):
                raise Exception(tr("Pathname {1} already exists. File {0} would not be moved.")\
                                .format(abs_src_path, abs_dst_path))            
                    
        self._session.flush()
        
        #TODO Если элемент реально не изменился, сохранять в историю ничего не нужно!!!
        #Сохраняем историю изменения данного элемента
        #UnitOfWork._save_history_rec(self._session, item_0, operation=HistoryRec.UPDATE, \
        #                             parent1_id = parent_hr.id, user_login=user_login)
        
        self._session.refresh(item_0)
        
        hr = HistoryRec(item_id = item_0.id, item_hash=item_0.hash(), \
                        operation=HistoryRec.UPDATE, \
                        user_login=user_login, \
                        parent1_id=parent_hr.id)
        if item_0.data_ref is not None:
            hr.data_ref_hash = item_0.data_ref.hash
            hr.data_ref_url = item_0.data_ref.url    
        if parent_hr != hr:
            self._session.add(hr)
        
        self._session.flush()
        
        print(str(parent_hr))
        print(str(hr))
                
        
        #Копируем или перемещаем файл (если необходимо, конечно)
        if need_file_operation == "copy" and item_0.data_ref.type == DataRef.FILE:
            if abs_src_path != os.path.join(self._repo_base_path, item_0.data_ref.url):
                shutil.copy(abs_src_path, os.path.join(self._repo_base_path, item_0.data_ref.url))
        elif need_file_operation == "move" and item_0.data_ref.type == DataRef.FILE:
            #Теперь начинаем перемещение файла
            shutil.move(abs_src_path, abs_dst_path)
            
        self._session.commit()
        
        self._session.refresh(item_0)
        self._session.expunge(item_0)
        return item_0
    
        
    def _prepare_data_ref(self, data_ref, user_login):
        
        def _prepare_data_ref_url(dr):                   
            #Нормализация пути
            dr.url = os.path.normpath(dr.url)
            #Убираем слеш, если есть в конце пути
            if dr.url.endswith(os.sep):
                dr.url = dr.url[0:len(dr.url)-1]
            #Определяем, находится ли данный файл уже внутри хранилища
            if is_internal(dr.url, self._repo_base_path):
                #Файл уже внутри
                #Делаем путь dr.url относительным и всё
                #Если dr.dst_path имеет непустое значение --- оно игнорируется!
                #TODO Как сделать, чтобы в GUI это было понятно пользователю?
                dr.url = os.path.relpath(dr.url, self._repo_base_path)
            else:
                #Файл снаружи                
                if not is_none_or_empty(dr.dst_path):            
                    #Такой файл будет скопирован в хранилище в директорию dr.dst_path
                    dr.url = os.path.join(dr.dst_path, os.path.basename(dr.url))
                else:
                    #Если dst_path пустая, тогда копируем в корень хранилища
                    dr.url = os.path.basename(dr.url)
        
        #Привязываем к пользователю
        data_ref.user_login = user_login
                
        #Запоминаем размер файла
        data_ref.size = os.path.getsize(data_ref.url)
        
        #Вычисляем хеш. Это может занять продолжительное время...
        data_ref.hash = compute_hash(data_ref.url)
        data_ref.date_hashed = datetime.datetime.today()
        
        #Делаем путь относительным, относительно корня хранилища
        _prepare_data_ref_url(data_ref)
    
    def delete_item(self, item_id, user_login, delete_physical_file=True):
        
        #TODO Нужно учесть, что при удалении элемента Item, в таблице HistoryRec
        #остаются висячие ссылки! Что делать? Может не удалять Item, а только помечать его как удаленный?
        #чтобы значение Item.id оставалось занятым. 
        
        #TODO Если user_login является админом, то ему можно удалять любые файлы
        
        item = self._session.query(Item).get(item_id)
        if item.user_login != user_login:
            raise AccessError(tr("Cannot delete item id={0} because it is owned by another user {1}.").format(item_id, item.user_login))
        
        if item.has_tags_except_of(user_login):
            raise AccessError(tr("Cannot delete item id={0} because another user tagged it.").format(item_id))
        
        if item.has_fields_except_of(user_login):
            raise AccessError(tr("Cannot delete item id={0} because another user attached a field to it.").format(item_id))
        
        #TODO Можно сделать и так, что если удаляешь элемент, а к нему прикреплен тег
        #другого пользователя, то элемент просто переходит во владение к этому пользователю
        #и у элемента удаляются все теги/поля первого пользователя.
        
        #Нужно взять из истории запись, соответствующую состоянию удаляемого объекта item
        parent_hr = UnitOfWork._find_item_latest_history_rec(self._session, item)
        #Если parent_hr равен None, то сохранять информацию об удалении может не надо?            
        if parent_hr is None:
            #Лучше выкинуть исключение
            raise Exception(tr("Cannot find corresponding history record for item id={0}.").format(item.id))
        
        #Запоминаем объект
        data_ref = item.data_ref
        
        #Сохраняем в историю запись о совершенной операции (если что не так, то rollback откатит все назад)
        UnitOfWork._save_history_rec(self._session, item, user_login, HistoryRec.DELETE, parent_hr.id)
        
        #Отвязываем элемент от data_ref-объекта (потому, что data_ref объект возможно надо будет удалить) 
        #и помечаем элемент как удаленный
        item.data_ref = None
        item.data_ref_id = None
        item.alive = False
        self._session.flush()
        #Все связанные ItemTag и ItemField объекты тоже остаются в базе
        
        #Если сохранять запись в историю операций тут, то не сохраняется путь и хеш файла!!!
        
        #Если на data_ref больше нет ссылок, то его будем удалять
        
        #Пытаться удалять data_ref нужно только если он имеется
        delete_data_ref = data_ref is not None
        
        #Нужно узнать, принадлежит ли data_ref пользователю user_login
        #Если нет, то удалять data_ref нельзя
        if delete_data_ref and data_ref.user_login != user_login:
            delete_data_ref = False
            
        if delete_data_ref:
            #Нужно узнать, есть ли другие элементы, которые ссылаются на данный data_ref
            #Если есть, то data_ref и файл удалять нельзя
            another_item = self._session.query(Item).filter(Item.data_ref==data_ref).first()
            if another_item:
                delete_data_ref = False
        
        if delete_data_ref:
            #Запоминаем кое-что
            is_file = data_ref.type == DataRef.FILE
            abs_path = os.path.join(self._repo_base_path, data_ref.url)
            
            #Удаляем data_ref из БД
            self._session.delete(data_ref)
            self._session.flush()
            
            #Теперь пробуем удалить физический файл
            if is_file and delete_physical_file and os.path.exists(abs_path):
                os.remove(abs_path)

        #Если все получилось --- завершаем транзакцию                
        self._session.commit()
        
        
    
    def save_new_item(self, item, user_login):
        
        if is_none_or_empty(user_login):
            raise AccessError(tr("Argument user_login shouldn't be null or empty."))
            
        
        #Предварительная обработка объекта Item
        item.user_login = user_login
        
        #Путь происхождения добавляемого файла. Именно отсюда файл будет скопирован внутрь хранилища
        data_ref_original_url = None
        
        #Предварительная обработка объекта DataRef
        if item.data_ref is not None:
            data_ref_original_url = item.data_ref.url            
            self._prepare_data_ref(item.data_ref, user_login)
            
                                                
        item_tags_copy = item.item_tags[:] #Копируем список
        existing_item_tags = []
        for item_tag in item_tags_copy:
            item_tag.user_login = user_login
            tag = item_tag.tag
            t = self._session.query(Tag).filter(Tag.name==tag.name).first()
            if t is not None:
                item_tag.tag = t
                existing_item_tags.append(item_tag)
                item.item_tags.remove(item_tag)
                
        item_fields_copy = item.item_fields[:] #Копируем список
        existing_item_fields = []
        for item_field in item_fields_copy:
            item_field.user_login = user_login
            field = item_field.field
            f = self._session.query(Field).filter(Field.name==field.name).first()
            if f is not None:
                item_field.field = f
                existing_item_fields.append(item_field)
                item.item_fields.remove(item_field)
        
        
    
        if item.data_ref is not None:
            dr = self._session.query(DataRef).filter(DataRef.url_raw==item.data_ref.url_raw).first()
            if dr is not None:
                raise Exception(tr("DataRef instance with url={}, "
                                   "already in database. "
                                   "Operation cancelled.").format(item.data_ref.url))
                #TODO Не выкидывать исключение, а привязывать к существующему объекту?
                #А вдруг имена совпадают, но содержимое файлов разное?

        #Сохраняем item пока что только с новыми тегами и новыми полями
        self._session.add(item)
        self._session.flush()
        
        #Добавляем в item существующие теги
        for it in existing_item_tags:
            item.item_tags.append(it)
        
        #Добавляем в item существующие поля
        for if_ in existing_item_fields:
            item.item_fields.append(if_)
            
        self._session.flush()
        
        
        #Сохраняем в БД data_ref объект
        if item.data_ref:          
            #Сохраняем data_ref в БД  
            self._session.add(item.data_ref)
            self._session.flush()
            
            #Привязываем к элементу            
            item.data_ref_id = item.data_ref.id
            self._session.flush()
        
        
        #Сохраняем запись о совершенной операции в историю
        UnitOfWork._save_history_rec(self._session, item, operation=HistoryRec.CREATE, \
                                     user_login=user_login)
        self._session.flush()
            
        #Если все сохранилось в БД, то копируем файл, связанный с DataRef
        if item.data_ref and item.data_ref.type == DataRef.FILE:
            dr = item.data_ref
            #Копируем, только если пути src и dst не совпадают, иначе это один и тот же файл!            
            abs_dst_path = os.path.join(self._repo_base_path, dr.url)
            if data_ref_original_url != abs_dst_path:

                #Если файл dst существует, то вылетает исключение                
                if os.path.exists(abs_dst_path):
                    raise FileAlreadyExistsError(tr("File {} already exists. Operation cancelled."))
                
                try:
                    head, tail = os.path.split(abs_dst_path)
                    os.makedirs(head)
                except:
                    pass
                shutil.copy(data_ref_original_url, abs_dst_path)
            else:
                #Это один и тот же файл, копировать не нужно ничего 
                pass
            
        self._session.commit()
    



class ItemIntegrityFixerThread(QtCore.QThread):
    '''
    Поток, выполняющий исправление целостности выбранной группы элементов (обычно из 
    результатов поискового запроса). 
    
    Нужно сделать функцию, чтобы запускать данный поток для выделенной группы элементов. 
    Для всех элементов хранилища тоже надо бы (но это потом может быть сделаю). 
    '''
    def __init__(self, parent, repo, items, lock, strategy, user_login):
        super(ItemIntegrityFixerThread, self).__init__(parent)
        self.repo = repo
        self.items = items
        
        #Замок, для того, чтобы поток смог изменять передаваемые ему объекты, содержащиеся в списке items
        self.lock = lock
        
        self.interrupt = False
        
        #Это словарь, в котором ключи - это коды ошибок, а значения - способ исправления данной ошибки
        self.strategy = strategy
        #Задавать стратегию исправления ошибок хотелось бы несложным образом:
        #strategy = {ERROR_FILE_NOT_FOUND: STRATEGY_1, ERROR_FILE_SIZE_MISMATCH: STRATEGY_2} и т.п.
        
        self.user_login = user_login
        
    
    def run(self):
        
        uow = self.repo.create_unit_of_work()
        
        fixers = dict()
        for error_code, strategy in self.strategy.items():
            fixers[error_code] = IntegrityFixer.create_fixer(error_code, strategy, uow, self.repo.base_path, self.lock)
        
        try:
            #Список self.items должен содержать только что извлеченные из БД элементы
            #(вместе с data_ref объектами).
            for i in range(len(self.items)):
                item = self.items[i]
                
                print("fixing item " + str(item.id))
                
                #Сначала смотрим, проверялся ли item на целостность данных?
                if item.error is None:
                    try:
                        self.lock.lockForWrite()
                        #Если нет, то проверяем                    
                        item.error = UnitOfWork._check_item_integrity(uow.session, item, self.repo.base_path)
                    finally:
                        self.lock.unlock()
                                
                #Смотрим, есть ли у item-а ошибки
                for error_code in list(item.error):
                    #Для каждой ошибки item-а нужно
                    #глянуть, есть ли стратегия исправления в поле self.strategy для данной ошибки?                
                    #если нет, то пропускаем, ничего не делаем
                    #если есть, то выполняем исправление ошибки
                    #сообщаем, что элемент нужно обновить
                    fixer = fixers.get(error_code)
                    if fixer is not None:
                        fixer.fix_error(item, self.user_login)
                        
                        #Сохраняем
                        uow.session.commit()
                        
                        try:
                            self.lock.lockForWrite()
                            #Убираем ошибку из списка
                            item.error.remove(error_code)
                        finally:
                            self.lock.unlock()
                            
                
                            
                
                #Снова проверяем целостность
                #item.error = UnitOfWork._check_item_integrity(uow.session, item, self.repo.base_path)

                self.emit(QtCore.SIGNAL("progress"), int(100.0*float(i)/len(self.items)), item.table_row)
                    
        except Exception as ex:
            print(traceback.format_exc())
            #self.emit(QtCore.SIGNAL("exception"), str(ex.__class__) + " " + str(ex))
            self.emit(QtCore.SIGNAL("exception"), sys.exc_info())
        finally:
            self.emit(QtCore.SIGNAL("finished"))
            uow.close()
            print("ItemIntegrityFixerThread done.")


       
class ItemIntegrityCheckerThread(QtCore.QThread):
    '''
    Поток, выполняющий в фоне проверку целостности группы элементов (обычно 
    результатов поискового запроса). 
    
    Нужно сделать функцию, чтобы запускать данный поток для выделенной группы элементов. 
    Для всех элементов хранилища тоже надо бы (но это потом может быть сделаю). 
    '''
    def __init__(self, parent, repo, items, lock):
        super(ItemIntegrityCheckerThread, self).__init__(parent)
        self.repo = repo
        self.items = items
        self.lock = lock
        self.interrupt = False
    
    def run(self):
        error_count = 0
        uow = self.repo.create_unit_of_work()
        try:
            #Список self.items должен содержать только что извлеченные из БД элементы
            #(вместе с data_ref объектами).
            for i in range(len(self.items)):
                item = self.items[i]
                
                error_set = UnitOfWork._check_item_integrity(uow.session, item, self.repo._base_path)
                
                try:
                    self.lock.lockForWrite()
                    
                    #Сохраняем результат
                    item.error = error_set
                    
                    if len(error_set) > 0:                        
                        error_count += 1  
                    
                    self.emit(QtCore.SIGNAL("progress"), int(100.0*float(i)/len(self.items)), item.table_row)
                    
                finally:
                    self.lock.unlock()
                    
        except:
            print(traceback.format_exc())
        finally:
            self.emit(QtCore.SIGNAL("finished"), error_count)
            uow.close()
            print("ItemIntegrityCheckerThread done.")


class ThumbnailBuilderThread(QtCore.QThread):
    '''
    Поток, выполняющий построение миниатюр изображений и сохранение их в БД.
    
    Данный поток автоматически запускается после выполнение любого запроса элементов 
    (т.к. в результате любого запроса могут оказаться изображения.
    '''
    def __init__(self, parent, repo, items, lock):
        super(ThumbnailBuilderThread, self).__init__(parent)
        self.repo = repo
        self.items = items
        self.lock = lock
        self.interrupt = False

    def run(self):
        #TODO Какой-то тут код... надо подумать, что улучшить тут
        uow = self.repo.create_unit_of_work()
        try:
            thumbnail_size = int(UserConfig().get("thumbnail_size", consts.THUMBNAIL_DEFAULT_SIZE))
            
            for i in range(len(self.items)):
                item = self.items[i]
                
                if self.interrupt:
                    print("ThumbnailBuilderThread interrupted!")
                    break
                
                if len(item.data_ref.thumbnails) > 0:
                    continue
            
                if not item.data_ref.is_image():
                    continue
                
                pixmap = QtGui.QImage(os.path.join(self.repo.base_path, item.data_ref.url))
                if pixmap.isNull():
                    continue
                
                #Масштабируем изображение
                if (pixmap.height() > pixmap.width()):
                    pixmap = pixmap.scaledToHeight(thumbnail_size)
                else:
                    pixmap = pixmap.scaledToWidth(thumbnail_size)
                
                buffer = QtCore.QBuffer()
                buffer.open(QtCore.QIODevice.WriteOnly);
                pixmap.save(buffer, "JPG")
                
                try:
                    self.lock.lockForWrite()
                    th = Thumbnail()
                    th.data = buffer.buffer().data()
                    th.data_ref_id = item.data_ref.id
                    th.size = thumbnail_size
                    item.data_ref.thumbnails.append(th)
                    
                    try:
                        #Сохраняем миниатюру в БД
                        uow.save_thumbnail(item.data_ref.id, th)
                    except:
                        #Если не получилось сохранить, то все равно данный поток не прерываем 
                        print("Cannot save in DB thumbnail for image " + item.data_ref.url)
                        print(traceback.format_exc())
                    
                except:
                    print("Cannot generate thumbnail for " + item.data_ref.url)
                    continue
                else:
                    self.emit(QtCore.SIGNAL("one_more_thumbnail_ready"), i)
                    print("Generated thumbnail of " + item.data_ref.url)
                finally:
                    self.lock.unlock()
                
                
                    
        except:
            print(traceback.format_exc())
        finally:
            uow.close()
            print("ThumbnailBuilderThread done.")

       
class DeleteGroupOfItemsThread(QtCore.QThread):
    def __init__(self, parent, repo, item_ids, user_login):
        super(DeleteGroupOfItemsThread, self).__init__(parent)
        self.repo = repo
        self.item_ids = item_ids
        self.user_login = user_login
        self.errors = 0
        self.detailed_message = None
        
    def run(self):
        self.errors = 0
        self.detailed_message = ""
        uow = self.repo.create_unit_of_work()
        try:
            i = 0
            for id in self.item_ids:
                #Удаляем каждый item по одному
                try:
                    uow.delete_item(id, self.user_login)
                except AccessError as ex:
                    #У пользователя self.user_login нет прав удалять данный элемент
                    self.errors += 1
                    self.detailed_message += str(ex) + os.linesep
                    
                i = i + 1
                self.emit(QtCore.SIGNAL("progress"), int(100.0*float(i)/len(self.item_ids)))
                        
        except Exception as ex:
            self.emit(QtCore.SIGNAL("exception"), str(ex.__class__) + " " + str(ex))
            print(traceback.format_exc())
        finally:
            self.emit(QtCore.SIGNAL("finished"))
            uow.close()
        
class CreateGroupIfItemsThread(QtCore.QThread):
    def __init__(self, parent, repo, items):
        super(CreateGroupIfItemsThread, self).__init__(parent)
        self.repo = repo
        self.items = items
    
    def run(self):
        uow = self.repo.create_unit_of_work()
        try:
            i = 0
            for item in self.items:
                #Сохраняем каждый item в отдельности
                uow.save_new_item(item, item.user_login)
                i = i + 1
                self.emit(QtCore.SIGNAL("progress"), int(100.0*float(i)/len(self.items)))
    
        except Exception as ex:
            self.emit(QtCore.SIGNAL("exception"), str(ex.__class__) + " " + str(ex))
            print(traceback.format_exc())
        finally:
            self.emit(QtCore.SIGNAL("finished"))
            uow.close()
        

class UpdateGroupOfItemsThread(QtCore.QThread):
    
    def __init__(self, parent, repo, items):
        super(UpdateGroupOfItemsThread, self).__init__(parent)
        self.repo = repo
        self.items = items

    def run(self):
        uow = self.repo.create_unit_of_work()
        try:
            i = 0
            for item in self.items:
                #Редактируем каждый item
                uow.update_existing_item(item, item.user_login)
                i = i + 1
                self.emit(QtCore.SIGNAL("progress"), int(100.0*float(i)/len(self.items)))
                
        except Exception as ex:
            self.emit(QtCore.SIGNAL("exception"), str(ex.__class__) + " " + str(ex))
            print(traceback.format_exc())
        finally:
            self.emit(QtCore.SIGNAL("finished"))
            uow.close()
        
    
class BackgrThread(QtCore.QThread):
        
    def __init__(self, parent, callable, *args):
        super(BackgrThread, self).__init__(parent)
        self.args = args
        self.callable = callable
    
    def run(self):
        try:
            self.callable(*self.args)
        except Exception as ex:
            self.emit(QtCore.SIGNAL("exception"), str(ex.__class__) + " " + str(ex))
            print(traceback.format_exc())
        finally:
            self.emit(QtCore.SIGNAL("finished"))
            
        
        
#    def __init__(self, uow, item, user_login, parent=None):
#        super(Worker, self).__init__(parent)
#        self.uow = uow
#        self.item = item
#        self.user_login = user_login
#    
#    def run(self):
#        try:
#            self.uow.save_new_item(self.item, self.user_login)
#            self.emit(QtCore.SIGNAL("finished()"))
#        except Exception as ex:
#            self.emit(QtCore.SIGNAL("exception"), str(ex.__class__) + " " + str(ex))
#        finally:
#            #А может и не закрывать тут юнит?            
#            self.uow.close()
        
        
        


