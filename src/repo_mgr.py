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
from sqlalchemy.orm import sessionmaker, contains_eager,\
    joinedload_all
from db_schema import Base, Item, User, Tag, Field, Item_Tag, DataRef, Item_Field,\
    Thumbnail, HistoryRec
from exceptions import LoginError, AccessError, FileAlreadyExistsError,\
    CannotOpenRepoError, DataRefAlreadyExistsError, NotFoundError
import shutil
import datetime
from sqlalchemy.exc import ResourceClosedError
from user_config import UserConfig
import db_schema
import helpers
from file_browser import FileInfo


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
        

    def create_unit_of_work(self):
        return UnitOfWork(self.Session(), self.base_path)


class UnitOfWork(object):
    ''' This class allows you to open a working session with database (unit of work), 
    do some actions and close the session.
    
    Also this class has methods for executing operations with the database. 
    TODO: This operations should be 
    moved to a separate Command classes (I think).
    '''
    
    #TODO argument repo_base_path should be moved to Command class ctor
    def __init__(self, session, repo_base_path):
        self._session = session
        self._repo_base_path = repo_base_path 
        
    def __del__(self):
        if self._session is not None:
            self._session.close()
        
    def close(self):
        self._session.expunge_all()
        self._session.close()
        
    @property
    def session(self):
        return self._session
        
#    def delete_all_thumbnails(self, data_ref_id):
#        rows = self._session.query(Thumbnail).filter(Thumbnail.data_ref_id==data_ref_id)\
#            .delete(synchronize_session="fetch")        
#        self._session.commit()
#        
#        return rows
        
    def save_thumbnail(self, data_ref_id, thumbnail):
        data_ref = self._session.query(DataRef).get(data_ref_id)
        self._session.refresh(data_ref)
        thumbnail.data_ref_id = data_ref.id
        print("len(data_ref.thumbnails) = {}".format(len(data_ref.thumbnails)))
        for th in data_ref.thumbnails:
            print(th)
        data_ref.thumbnails.append(thumbnail)
        self._session.add(thumbnail)
        
        self._session.commit()
        
        self._session.refresh(thumbnail)
        self._session.expunge(thumbnail)
        self._session.expunge(data_ref)
        
        
        
    def get_related_tags(self, tag_names=[], user_logins=[], limit=0):
        ''' Возвращает список related тегов для тегов из списка tag_names.
        Если tag_names - пустой список, возращает все теги.
        Поиск ведется среди тегов пользователей из списка user_logins.
        Если user_logins пустой, то поиск среди всех тегов в БД.
        
        limit affects only if tag_names is empty. In other cases limit is ignored.
        If limit == 0 it means there is no limit.
        '''
        
        #TODO Пока что не учитывается аргумент user_logins
        
        if len(tag_names) == 0:
            #TODO The more items in the repository, the slower this query is performed.
            #I think, I should store in database some statistics information, such as number of items
            #tagged with each tag. With this information, the query can be rewritten and became much faster.
            if limit > 0:
                sql = '''
                select name, c 
                from
                (select t.name as name, count(*) as c
                   from items i, tags t
                   join items_tags it on it.tag_id = t.id and it.item_id = i.id and i.alive   
                where
                    1
                group by t.name
                ORDER BY c DESC LIMIT ''' + str(limit) + ''') as sub
                ORDER BY name
                '''
            else:
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
            try:
                tags = self._session.query(Tag).from_statement(sql).all()
            except ResourceClosedError:
                tags = []
            tag_ids = []
            for tag in tags:
                tag_ids.append(tag.id)
                
            if len(tag_ids) == 0:
                #TODO Maybe raise an exception?
                return []
            
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
    
    def get_names_of_all_tags_and_fields(self):
        sql = '''
        select distinct name from tags
        UNION
        select distinct name from fields
        ORDER BY name
        '''
        try:            
            return self._session.query("name").from_statement(sql).all()
        except ResourceClosedError:
            return []
        
    
    def get_file_info(self, path):
        data_ref = self._session.query(DataRef)\
            .filter(DataRef.url_raw==helpers.to_db_format(path))\
            .options(joinedload_all("items"))\
            .options(joinedload_all("items.item_tags.tag"))\
            .options(joinedload_all("items.item_fields.field"))\
            .one()
        self._session.expunge(data_ref)
        finfo = FileInfo(data_ref.url, status = FileInfo.STORED_STATUS)
        
        for item in data_ref.items:            
            for item_tag in item.item_tags:
                if item_tag.user_login not in finfo.user_tags: #finfo.user_tags is a dict()
                    finfo.user_tags[item_tag.user_login] = []
                finfo.user_tags[item_tag.user_login].append(item_tag.tag.name)
            
            for item_field in item.item_fields:
                if item_field.user_login not in finfo.user_fields:
                    finfo.user_fields[item_field.user_login] = dict()
                finfo.user_fields[item_field.user_login][item_field.field.name] = item_field.field_value 
                
        return finfo
    
    def getExpungedItem(self, id):
        '''Returns expunged (detached) object of Item class from database with given id.'''
        item = self._session.query(Item)\
            .options(joinedload_all('data_ref'))\
            .options(joinedload_all('item_tags.tag'))\
            .options(joinedload_all('item_fields.field'))\
            .get(id)
            
        if item is None:
            raise NotFoundError()
        
        self._session.expunge(item)
        return item
    
    def get_untagged_items(self, limit=0, page=1, order_by=""):
        '''
        Извлекает из БД все ЖИВЫЕ элементы, с которыми не связано ни одного тега.
        '''
        
        order_by_1 = ""
        order_by_2 = ""
        for col, dir in order_by:
            if order_by_1:
                order_by_1 += ", "
            if order_by_2:
                order_by_2 += ", "
            order_by_2 += col + " " + dir + " "
            if col == "title":
                order_by_1 += col + " " + dir + " "
        if order_by_1:
            order_by_1 = " ORDER BY " + order_by_1
        if order_by_2:
            order_by_2 = " ORDER BY " + order_by_2
        
        thumbnail_default_size = UserConfig().get("thumbnail_size", consts.THUMBNAIL_DEFAULT_SIZE)
        
        
        if page < 1:
            raise ValueError("Page number cannot be negative or zero.")
        
        if limit < 0:
            raise ValueError("Limit cannot be negative number.")
        
        limit_offset = ""
        if limit > 0:
            offset = (page-1)*limit
            limit_offset += "LIMIT {0} OFFSET {1}".format(limit, offset)
        
        
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
            left join thumbnails on data_refs.id = thumbnails.data_ref_id and thumbnails.size = ''' + str(thumbnail_default_size) + ''' 
            where 
                it.item_id is null
                AND i.alive
            ''' + order_by_1 + " " + limit_offset + ''' 
        ) as sub
        left join items_tags on sub.id = items_tags.item_id
        left join tags on tags.id = items_tags.tag_id
        left join items_fields on sub.id = items_fields.item_id
        left join fields on fields.id = items_fields.field_id         
        ''' + order_by_2
                
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
    
    def query_items_by_tree(self, query_tree, limit=0, page=1, order_by=[]):
        '''
        Функция извлекает item-ы, которые соответствуют дереву разбора query_tree.
        '''
        
        order_by_1 = ""
        order_by_2 = ""
        for col, dir in order_by:
            if order_by_1:
                order_by_1 += ", "
            if order_by_2:
                order_by_2 += ", "
            order_by_2 += col + " " + dir + " "
            if col == "title":
                order_by_1 += col + " " + dir + " "
        if order_by_1:
            order_by_1 = " ORDER BY " + order_by_1
        if order_by_2:
            order_by_2 = " ORDER BY " + order_by_2
            
        
        sub_sql = query_tree.interpret()
        
        if page < 1:
            raise ValueError("Page number cannot be negative or zero.")
        
        if limit < 0:
            raise ValueError("Limit cannot be negative number.")
        
        limit_offset = ""
        if limit > 0:
            offset = (page-1)*limit
            limit_offset += "LIMIT {0} OFFSET {1}".format(limit, offset)
        
        sql = '''
        select sub.*, 
        ''' + db_schema.Item_Tag._sql_from() + ''', 
        ''' + db_schema.Tag._sql_from() + ''',
        ''' + db_schema.Thumbnail._sql_from() + ''',
        ''' + db_schema.Item_Field._sql_from() + ''',
        ''' + db_schema.Field._sql_from() + '''        
        from (''' + sub_sql + " " + order_by_1 + " " + limit_offset +  ''') as sub
        left join items_tags on sub.id = items_tags.item_id
        left join tags on tags.id = items_tags.tag_id
        left join items_fields on sub.id = items_fields.item_id
        left join fields on fields.id = items_fields.field_id
        left join thumbnails on thumbnails.data_ref_id = sub.data_refs_id and 
                  thumbnails.size = ''' + str(UserConfig().get("thumbnail_size", consts.THUMBNAIL_DEFAULT_SIZE)) + '''
        where sub.alive        
        ''' + order_by_2
        
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
                hash = helpers.compute_hash(abs_path)
                size = os.path.getsize(abs_path)
                if item.data_ref.hash != hash or item.data_ref.size != size:
                    error_set.add(Item.ERROR_FILE_HASH_MISMATCH)                
        
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
            data_ref_url = item_0.data_ref.url_raw
        parent_hr = session.query(HistoryRec).filter(HistoryRec.item_id==item_0.id)\
                .filter(HistoryRec.item_hash==item_0.hash())\
                .filter(HistoryRec.data_ref_hash==data_ref_hash)\
                .filter(HistoryRec.data_ref_url_raw==data_ref_url)\
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
    
    
    
    
    def updateExistingItem(self, item, user_login):
        ''' item - is a detached object, representing a new state for stored item with id == item.id.
            user_login - is a login of user, who is doing the modifications of the item.
            Returns detached updated item or raises an exception, if something goes wrong. 
        
            If item.data_ref.url is changed --- that means that user wants this item 
        to reference to another file. 
            If item.data_ref.dstRelPath is not None --- that means that user wants
        to move (and maybe rename) original referenced file withing the repository.
        
        TODO: Maybe we should use item.data_ref.srcAbsPath instead of item.data_ref.url... ?
        TODO: We should deny any user to change tags/fields/files of items, owned by another user.   
        '''
        
        persistentItem = self._session.query(Item).get(item.id)
        
        
        parent_hr = UnitOfWork._find_item_latest_history_rec(self._session, persistentItem)
        if parent_hr is None:
            raise Exception(tr("HistoryRec for Item object id={0} not found.").format(persistentItem.id))
            #TODO Пользователю нужно сказать, чтобы он вызывал функцию проверки целостности и исправления ошибок
        
        #Here we update simple data memers of item
        persistentItem.title = item.title
        persistentItem.user_login = item.user_login
        self._session.flush()
                        
        self.__updateTags(item, persistentItem, user_login)
        
        self.__updateFields(item, persistentItem, user_login)
        
        srcAbsPath = None
        if persistentItem.data_ref is not None:
            srcAbsPath = os.path.join(self._repo_base_path, persistentItem.data_ref.url)
        else:
            srcAbsPath = item.data_ref.url
            
        need_file_operation = self.__updateDataRefObject(item, persistentItem, user_login)
        
        
        self._session.refresh(persistentItem)
        
        
        # Now we should update History Records
        # TODO: we shouldn't touch History Records if the item hasn't changed
        hr = HistoryRec(item_id = persistentItem.id, item_hash=persistentItem.hash(), \
                        operation=HistoryRec.UPDATE, \
                        user_login=user_login, \
                        parent1_id=parent_hr.id)
        if persistentItem.data_ref is not None:
            hr.data_ref_hash = persistentItem.data_ref.hash
            hr.data_ref_url = persistentItem.data_ref.url    
        if parent_hr != hr:
            self._session.add(hr)
        self._session.flush()
        
        
        # Perform operations with the file in os filesystem
        dstAbsPath2 = os.path.join(self._repo_base_path, persistentItem.data_ref.url)
        if not is_none_or_empty(need_file_operation) and srcAbsPath != dstAbsPath2:
            if not os.path.exists(os.path.split(dstAbsPath2)[0]):
                os.makedirs(os.path.split(dstAbsPath2)[0])    
            if need_file_operation == "copy" and persistentItem.data_ref.type == DataRef.FILE:
                    shutil.copy(srcAbsPath, dstAbsPath2)
            elif need_file_operation == "move" and persistentItem.data_ref.type == DataRef.FILE:
                shutil.move(srcAbsPath, os.path.split(dstAbsPath2)[0])
        
        self._session.commit()
        
        self._session.refresh(persistentItem)
        self._session.expunge(persistentItem)
        return persistentItem
    
    def __updateTags(self, item, persistentItem, user_login):
        # Removing tags
        for itag in persistentItem.item_tags:
            i = index_of(item.item_tags, lambda x: True if x.tag.name==itag.tag.name else False)
            if i is None:
                #NOTE: Tag object would still persist in DB (even if no items would use it)
                self._session.delete(itag)
        self._session.flush()
        
        # Adding tags
        for itag in item.item_tags:
            i = index_of(persistentItem.item_tags, lambda x: True if x.tag.name==itag.tag.name else False)
            if i is None:
                tag = self._session.query(Tag).filter(Tag.name==itag.tag.name).first()
                if tag is None:
                    # Such a tag is not in DB yet
                    tag = Tag(itag.tag.name)
                    self._session.add(tag)
                    self._session.flush()
                # Link the tag with the item
                item_tag = Item_Tag(tag, user_login)
                self._session.add(item_tag)
                item_tag.item = persistentItem
                persistentItem.item_tags.append(item_tag)
        self._session.flush() 
    
    def __updateFields(self, item, persistentItem, user_login):
        # Removing fields
        for ifield in persistentItem.item_fields:
            i = index_of(item.item_fields, lambda o: True if o.field.name==ifield.field.name else False)
            if i is None:
                self._session.delete(ifield)
        self._session.flush()
        
        # Adding fields
        for ifield in item.item_fields:
            i = index_of(persistentItem.item_fields, \
                         lambda o: True if o.field.name==ifield.field.name else False)
            if i is None:
                field = self._session.query(Field).filter(Field.name==ifield.field.name).first()
                if field is None: 
                    field = Field(ifield.field.name)
                    self._session.add(field)
                    self._session.flush()
                item_field = Item_Field(field, ifield.field_value, user_login)
                self._session.add(item_field)
                item_field.item = persistentItem
                persistentItem.item_fields.append(item_field)
            elif ifield.field_value != persistentItem.item_fields[i].field_value:
                # Item already has such a field, we should just change it's value
                self._session.add(persistentItem.item_fields[i])
                persistentItem.item_fields[i].field_value = ifield.field_value
        self._session.flush()
    
    def __updateDataRefObject(self, item, persistentItem, user_login):
        # Processing DataRef object 
        srcAbsPath = None
        dstAbsPath = None
        need_file_operation = None
        
        if item.data_ref is None:
            # User removed the DataRef object from item (or it was None before..)
            #TODO Maybe remove DataRef if there are no items that reference to it?
            persistentItem.data_ref = None
            persistentItem.data_ref_id = None
        elif persistentItem.data_ref is None or persistentItem.data_ref.url != item.data_ref.url:
            # The item is attached to DataRef object at the first time or
            # it changes his DataRef object to another DataRef object
            
            url = item.data_ref.url
            if item.data_ref.type == DataRef.FILE:
                assert os.path.isabs(url), "item.data_ref.url should be an absolute path"
                url = os.path.relpath(url, self._repo_base_path)
                
            existing_data_ref = self._session.query(DataRef).filter(DataRef.url_raw==helpers.to_db_format(url)).first()            
            if existing_data_ref is not None:
                persistentItem.data_ref = existing_data_ref
            else:
                #We should create new DataRef object in this case                
                self._prepare_data_ref(item.data_ref, user_login)
                self._session.add(item.data_ref)
                self._session.flush()
                persistentItem.data_ref = item.data_ref
                if item.data_ref.type == DataRef.FILE:
                    need_file_operation = "copy"
                
        elif item.data_ref.type == DataRef.FILE and not is_none_or_empty(item.data_ref.dstRelPath):
            # A file referenced by the item is going to be moved to some another location
            # within the repository. item.data_ref.dstRelPath is the new relative
            # path to this file. File will be copied.
            
            srcAbsPath = os.path.join(self._repo_base_path, persistentItem.data_ref.url)
            dstAbsPath = os.path.join(self._repo_base_path, item.data_ref.dstRelPath)
            if not os.path.exists(srcAbsPath):
                raise Exception(tr("File {0} not found!").format(srcAbsPath))
            
            if os.path.exists(dstAbsPath):
                raise Exception(tr("Pathname {0} already exists. File {1} would not be moved.")\
                                .format(dstAbsPath, srcAbsPath))
                
            if os.path.abspath(srcAbsPath) == os.path.abspath(dstAbsPath):
                raise Exception(tr("Destination path {0} should be different from item's DataRef.url {1}")
                                .format(dstAbsPath, srcAbsPath))
            
            persistentItem.data_ref.url = item.data_ref.dstRelPath
            need_file_operation = "move"
        self._session.flush()
        return need_file_operation
                
    
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
                #Если dr.dstRelPath имеет непустое значение --- оно игнорируется!
                #TODO Как сделать, чтобы в GUI это было понятно пользователю?
                dr.url = os.path.relpath(dr.url, self._repo_base_path)
            else:
                #Файл снаружи                
                if not is_none_or_empty(dr.dstRelPath) and dr.dstRelPath != ".":
                    dr.url = dr.dstRelPath
                    #TODO insert check to be sure that dr.dstRelPath inside a repository!!!
                else:
                    #Если dstRelPath пустая или равна ".", тогда копируем в корень хранилища
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
    
    def deleteItem(self, item_id, user_login, delete_physical_file=True):
        # We should not delete Item objects from database, because
        # we do not want hanging references in HistoryRec table.
        # So we just mark Items as deleted. 
        
        # DataRef objects are deleted from database, if there are no references to it from other alive Items.
        
        # TODO: Make admin users to be able to delete any files, owned by anybody.
        
        item = self._session.query(Item).get(item_id)
        if item.user_login != user_login:
            raise AccessError(tr("Cannot delete item id={0} because it is owned by another user {1}.")
                              .format(item_id, item.user_login))
        
        if item.has_tags_except_of(user_login):
            raise AccessError(tr("Cannot delete item id={0} because another user tagged it.")
                              .format(item_id))
        
        if item.has_fields_except_of(user_login):
            raise AccessError(tr("Cannot delete item id={0} because another user attached a field to it.")
                              .format(item_id))
        
        parent_hr = UnitOfWork._find_item_latest_history_rec(self._session, item)            
        if parent_hr is None:
            raise Exception(tr("Cannot find corresponding history record for item id={0}.")
                            .format(item.id))
        
        data_ref = item.data_ref

        UnitOfWork._save_history_rec(self._session, item, user_login, HistoryRec.DELETE, parent_hr.id)
        
        item.data_ref = None
        item.data_ref_id = None
        item.alive = False
        self._session.flush()
        #All bounded ItemTag and ItemField objects stays in database with the Item 
        
        #If data_ref is not referenced by other Items, we delete it
        
        delete_data_ref = data_ref is not None
        
        #We should not delete DataRef if it is owned by another user
        if delete_data_ref and data_ref.user_login != user_login:
            delete_data_ref = False
            
        if delete_data_ref:
            another_item = self._session.query(Item).filter(Item.data_ref==data_ref).first()
            if another_item:
                delete_data_ref = False
        
        if delete_data_ref:
            is_file = (data_ref.type == DataRef.FILE)
            abs_path = os.path.join(self._repo_base_path, data_ref.url)
            
            self._session.delete(data_ref)
            self._session.flush()
            
            if is_file and delete_physical_file and os.path.exists(abs_path):
                os.remove(abs_path)

        self._session.commit()
        
        
    def saveNewItem(self, item, srcAbsPath=None, dstRelPath=None):
        '''Method saves in database given item.
        Returns id of created item, or raises an exception if something wrong.
        When this function returns, item object is expunged from the current Session.
            item.user_login - specifies owner of this item (and all tags/fields linked with it).
            srcAbsPath - absolute path to a file which will be referenced by this item.
            dstRelPath - relative (to repository root) path where to put the file.
        File is always copyied from srcAbsPath to <repo_base_path>/dstRelPath, except when 
        srcAbsPath is the same as <repo_base_path>/dstRelPath.
        
        Use cases:
                0) Both srcAbsPath and dstRelPath are None, so User wants to create an Item 
            without DataRef object.
                1) User wants to add an external file into the repo. File is copied to the 
            repo.
                2) There is an untracked file inside the repo tree. User wants to add such file 
            into the repo to make it a stored file. File is not copied, because it is alredy in 
            the repo tree.
                3) User wants to add a copy of a stored file from the repo into the same repo 
            but to the another location. Original file is copyied. The copy of the original file 
            will be attached to the new Item object.
                4) ERROR: User wants to attach to a stored file another new Item object.
            This is FORBIDDEN! Because existing item may be not integral with the file.
            TODO: We can allow this operation only if integrity check returns OK. May be implemented
            in the future.
            
            NOTE: Use cases 1,2,3 require creation of a new DataRef object.
            If given item has not null item.data_ref object, it is ignored anyway.
        '''
        
        isDataRefRequired = not is_none_or_empty(srcAbsPath)
        if isDataRefRequired:
            assert(dstRelPath is not None) 
            #NOTE: If dstRelPath is an empty string it means the root of repository
        
            srcAbsPath = os.path.normpath(srcAbsPath)
            if not os.path.isabs(srcAbsPath):
                raise ValueError(tr("srcAbsPath must be an absolute path."))
            
            if not os.path.exists(srcAbsPath):
                raise ValueError(tr("srcAbsPath must point to an existing file."))
            
            if os.path.isabs(dstRelPath):
                raise ValueError(tr("dstRelPath must be a relative to repository root path."))
            
            dstRelPath = helpers.removeTrailingOsSeps(dstRelPath)
            dstRelPath = os.path.normpath(dstRelPath)
            dstAbsPath = os.path.abspath(os.path.join(self._repo_base_path, dstRelPath))
            dstAbsPath = os.path.normpath(dstAbsPath)
            if srcAbsPath != dstAbsPath and os.path.exists(dstAbsPath):
                raise ValueError(tr("{} should not point to an existing file.").format(dstAbsPath))
                
            dataRef = self._session.query(DataRef).filter(
                DataRef.url_raw==helpers.to_db_format(dstRelPath)).first()
            if dataRef is not None:
                raise DataRefAlreadyExistsError(tr("DataRef instance with url='{}' "
                                                   "already in database. ").format(dstRelPath))
        
        user_login = item.user_login
        if is_none_or_empty(user_login):
            raise AccessError(tr("Argument user_login shouldn't be null or empty."))
        
        user = self._session.query(db_schema.User).get(user_login)
        if user is None:
            raise AccessError(tr("User with login {} doesn't exist.").format(user_login))
        
                
        #Remove from item those tags, which have corresponding Tag objects in database
        item_tags_copy = item.item_tags[:] #Making list copy
        existing_item_tags = []
        for item_tag in item_tags_copy:
            item_tag.user_login = user_login
            tag = item_tag.tag
            t = self._session.query(Tag).filter(Tag.name==tag.name).first()
            if t is not None:
                item_tag.tag = t
                existing_item_tags.append(item_tag)
                item.item_tags.remove(item_tag)
                
        #Remove from item those fields, which have corresponding Field objects in database
        item_fields_copy = item.item_fields[:] #Making list copy
        existing_item_fields = []
        for item_field in item_fields_copy:
            item_field.user_login = user_login
            field = item_field.field
            f = self._session.query(Field).filter(Field.name==field.name).first()
            if f is not None:
                item_field.field = f
                existing_item_fields.append(item_field)
                item.item_fields.remove(item_field)
                
        #Saving item with just absolutely new tags and fields
        self._session.add(item)
        self._session.flush()
        
        #Adding to the item existent tags
        for it in existing_item_tags:
            item.item_tags.append(it)
        #Adding to the item existent fields
        for if_ in existing_item_fields:
            item.item_fields.append(if_)
        #Saving item with existent tags and fields
        self._session.flush()
        
        
        if isDataRefRequired:
            item.data_ref = DataRef(type=DataRef.FILE, url=dstRelPath)
            item.data_ref.user_login = user_login
            item.data_ref.size = os.path.getsize(srcAbsPath)
            item.data_ref.hash = compute_hash(srcAbsPath)
            item.data_ref.date_hashed = datetime.datetime.today()
            self._session.add(item.data_ref)
            self._session.flush()
            
            item.data_ref_id = item.data_ref.id
            self._session.flush()
        else:
            item.data_ref = None
        
        #Saving HistoryRec object about this CREATE new item operation
        UnitOfWork._save_history_rec(self._session, item, operation=HistoryRec.CREATE, \
                                     user_login=user_login)
        self._session.flush()
        
        #Now it's time to COPY physical file to the repository
        if isDataRefRequired and srcAbsPath != dstAbsPath:
            try:
                #Making dirs
                head, tail = os.path.split(dstAbsPath)
                os.makedirs(head)
            except:
                pass
            shutil.copy(srcAbsPath, dstAbsPath)
            #TODO should not use shutil.copy() function, because I cannot specify block size! 
            #On very large files (about 15Gb) shutil.copy() function takes really A LOT OF TIME.
            #Because of small block size, I think.
        
        self._session.commit()
        item_id = item.id
        self._session.expunge(item)
        return item_id

        
    



