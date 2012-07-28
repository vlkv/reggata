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

Created on 11.10.2010

Схема базы данных хранилища метаданных Reggata.
'''

import sqlalchemy as sqa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, orm
from helpers import tr, is_none_or_empty
import datetime
import os
import platform
import hashlib
import helpers
import memento



Base = declarative_base()


class User(Base):
    '''
    Пользователь системы reggata.
    '''
    __tablename__ = "users"
    
    USER = 'USER'
    ADMIN = 'ADMIN'
    
    login = sqa.Column(sqa.String, primary_key=True)
    password = sqa.Column(sqa.String)
    group = sqa.Column(sqa.Enum(USER, ADMIN), nullable=False, default=USER)
    date_created = sqa.Column(sqa.DateTime)
    
    def check_valid(self):
        if self.login is None or self.login=="":
            raise ValueError(tr("Attribute User.login shouldn't be empty."))        
        return True



#Таблица связей Tag и Item
#tags_items = sqa.Table('tags_items', Base.metadata,
#    sqa.Column('item_id', sqa.Integer, ForeignKey('items.id'), primary_key=True),
#    sqa.Column('tag_name', sqa.String, primary_key=True),
#    sqa.Column('tag_user_login', sqa.String, primary_key=True),
#    ForeignKeyConstraint(['tag_name', 'tag_user_login'], ['tags.name', 'tags.user_login'])
#)


class HistoryRec(Base):
    '''
    Запись об одном элементе в истории изменения хранилища.
    '''
    
    __tablename__ = "history_recs"
    
#    __table_args__ = (
#        UniqueConstraint("item_hash", "data_ref_hash", "data_ref_url"),
#        {}
#    )
    
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    MERGE = "MERGE"
    
    id = sqa.Column(sqa.Integer, primary_key=True)
    parent1_id = sqa.Column(sqa.Integer, ForeignKey("history_recs.id"))
    parent2_id = sqa.Column(sqa.Integer, ForeignKey("history_recs.id"))
    item_id = sqa.Column(sqa.Integer, ForeignKey("items.id"))
    item_hash = sqa.Column(sqa.String)
    data_ref_hash = sqa.Column(sqa.String)
    data_ref_url_raw = sqa.Column(sqa.String, name="data_ref_url")
    operation = sqa.Column(sqa.Enum(CREATE, UPDATE, DELETE, MERGE))
    user_login = sqa.Column(sqa.String, ForeignKey("users.login"))
    
    #TODO Сюда можно сохранять и дату/время, однако, на эти данные нельзя полагаться
    #на разных машинах может быть разное время (плюс минус погрешность или вообще неверное)
    
    def __init__(self, item_id=None, item_hash=None, data_ref_hash=None, \
                 data_ref_url=None, operation=None, user_login=None, \
                 parent1_id=None, parent2_id=None):
        self.item_id = item_id
        self.item_hash = item_hash
        self.data_ref_hash = data_ref_hash
        self.data_ref_url = data_ref_url
        self.operation = operation
        self.user_login = user_login
        self.parent1_id = parent1_id 
        self.parent2_id = parent2_id

    def _get_data_ref_url(self):
        if not is_none_or_empty(self.data_ref_hash):
            #Если хеш непустой, то DataRef связан с физическим файлом
            return helpers.from_db_format(self.data_ref_url_raw)
        else:
            return self.data_ref_url_raw
    
    def _set_data_ref_url(self, value):
        if not is_none_or_empty(self.data_ref_hash):
            #Если хеш непустой, то DataRef связан с физическим файлом
            #Сохранять в БД этот url и  DataRef.url нужно всегда в формате Unix (т.е. с прямыми слешами) 
            self.data_ref_url_raw = helpers.to_db_format(value)
        else:
            self.data_ref_url_raw = value
      
    data_ref_url = property(_get_data_ref_url, _set_data_ref_url, 'Свойство data_ref_url.')

    def __eq__(self, obj):
        '''Проверка на равенство. Значения HistoryRec.id могут быть разными 
        (они не учитываются при сравнении. Также не учитываются поля parent1_id и parent2_id.
        Также не учитывается operation.
        Однако значения HistoryRec.item_id должны быть одинаковыми.        
        '''
        if self.item_id != obj.item_id:
            return False
        if self.item_hash != obj.item_hash:
            return False
        if self.data_ref_hash != obj.data_ref_hash:
            return False
        if self.data_ref_url != obj.data_ref_url:
            return False        
        if self.user_login != obj.user_login:
            return False
        
        return True
        
    def __ne__(self, obj):
        return not self.__eq__(obj)

    def __str__(self):
        s = "item_id={}, item_hash={}, data_ref_hash={}, data_ref_url={}, operation={}, user_login={}, parent1_id={}, parent2_id={}"\
            .format(self.item_id, self.item_hash, self.data_ref_hash, self.data_ref_url, self.operation, self.user_login, self.parent1_id, self.parent2_id)
        return s

class Item(Base, memento.Serializable):
    '''
    Элемент (запись, объект) хранилища.
    '''
    __tablename__ = "items"
        
    ERROR_FILE_NOT_FOUND = 1
    ERROR_FILE_HASH_MISMATCH = 2    
    ERROR_HISTORY_REC_NOT_FOUND = 4
    
    
    id = sqa.Column(sqa.Integer, primary_key=True)
    
    title = sqa.Column(sqa.String, nullable=False)
    
    user_login = sqa.Column(sqa.String, ForeignKey("users.login"))
    
    date_created = sqa.Column(sqa.DateTime)
    
    data_ref_id = sqa.Column(sqa.Integer, ForeignKey("data_refs.id"))
    
    #Удаляемые элементы, не будут удаляться из базы, им просто будет установлено значение alive=False
    alive = sqa.Column(sqa.Boolean, default=True)    
    
    #пользователь-владелец данного элемента
    user = relationship(User, cascade="merge, expunge, refresh-expire")
    
    #связанный файл/ссылка_URL
    data_ref = relationship("DataRef", cascade="merge, expunge, refresh-expire") #TODO Ведь не нужен тут save-update?
    
    #tags - список связанных тегов
    item_tags = relationship("Item_Tag", cascade="all, delete-orphan")
    
    #field_vals - список связанных полей
    item_fields = relationship("Item_Field", cascade="all, delete-orphan")

    def __init__(self, user_login=None, title=None, date_created=None, alive=True):
        self.alive = alive
        self.user_login = user_login
        self.title = title        
        if date_created is not None:
            self.date_created = date_created
        else:
            self.date_created = datetime.datetime.today()
                    
        self.error = None
        
            
    @orm.reconstructor
    def __init_on_load__(self):
        self.error = None #Если error равен None, то проверку целостности просто не проводили
        
    def __listOfTagsAndTheirOwners(self):
        return list((self.item_tags[i].tag.name, 
                     self.item_tags[i].user_login)
                    for i in range(len(self.item_tags)) )
        
    def __listOfFieldValsAndTheirOwners(self):
        return list((self.item_fields[i].field.name, 
                     self.item_fields[i].field_value, 
                     self.item_fields[i].user_login)
                    for i in range(len(self.item_fields)) )
        
    def toJson(self):
        return {"__class__": self.__class__.__name__,
                "__module__": "db_schema",
                "title": self.title,
                "user_login": self.user_login,
                "date_created": self.date_created,
                "tags": self.__listOfTagsAndTheirOwners(),
                "fields": self.__listOfFieldValsAndTheirOwners(),
                "data_ref": self.data_ref,
                }
        
    @staticmethod
    def fromJson(objState):
        item = Item()
        item.title = objState["title"]
        item.user_login = objState["user_login"]
        item.date_created = objState["date_created"]
        
        for (tag_name, tag_owner) in objState["tags"]:
            tag = Tag(tag_name)
            item.item_tags.append(Item_Tag(tag, tag_owner))
            
        for (field_name, field_val, field_owner) in objState["fields"]:
            field = Field(field_name)
            item.item_fields.append(Item_Field(field, field_val, field_owner))
        
        item.data_ref = objState["data_ref"]
        
        return item
    
    
    @staticmethod
    def format_error_set(error_set):
        
        if error_set is not None:
            if len(error_set) == 0:
                s = tr("No errors")
            else:
                s = ""
                for error in error_set:
                    if error == Item.ERROR_FILE_HASH_MISMATCH:
                        s += tr("err_{0}: file has changed (hash/size mismatch)").format(Item.ERROR_FILE_HASH_MISMATCH) + os.linesep
                    elif error == Item.ERROR_FILE_NOT_FOUND:
                        s += tr("err_{0}: file not found").format(Item.ERROR_FILE_NOT_FOUND) + os.linesep
                    elif error == Item.ERROR_HISTORY_REC_NOT_FOUND:
                        s += tr("err_{0}: item's history record not found").format(Item.ERROR_HISTORY_REC_NOT_FOUND) + os.linesep
                if s.endswith(os.linesep):
                    s = s[:-1]
        else:
            s = tr("Item integrity isn't checked yet")
            
        return s
    
    @staticmethod
    def format_error_set_short(error_set):

        if error_set is None:
            #Целостность не проверялась
            return ""
        if len(error_set) <= 0:
            #Ошибок нет, целостность в порядке
            return 'OK'
        elif len(error_set) > 0:
            #Есть ошибки
            return helpers.to_commalist(error_set, lambda x: "err_{0}".format(x))
            
        
        


    def hash(self):
        '''
        Метод вычисляет и возвращает хеш от данного элемента.
        '''
        
        text = ""
        
        if not is_none_or_empty(self.title):
            text += self.title
        
        if not is_none_or_empty(self.user_login):
            text += self.user_login
        
        if self.date_created is not None:
            text += str(self.date_created)
        
        #Связанные теги
        tag_names = []
        for item_tag in self.item_tags:
            tag_names.append(item_tag.tag.name)
        tag_names.sort()
        
        for tag_name in tag_names:
            text += tag_name        
        
        #Связанные поля:значения
        field_vals = []
        for item_field in self.item_fields:
            field_vals.append(item_field.field.name + str(item_field.field_value))
        field_vals.sort()
        
        for field_val in field_vals:
            text += field_val
        
        return hashlib.sha1(text.encode("utf-8")).hexdigest()
    
    def get_field_value(self, field_name, user_login=None):
        '''Returns value of field field_name. If no such field exists in this item, returns None.'''
        for item_field in self.item_fields:
            if item_field.field.name == field_name:
                if user_login is None or item_field.user_login == user_login:
                    return item_field.field_value
        return None
    
    def has_tags_except_of(self, user_login):
        for item_tag in self.item_tags:
            if item_tag.user_login != user_login:
                return True
        return False
    
    def has_fields_except_of(self, user_login):
        for item_field in self.item_fields:
            if item_field.user_login != user_login:
                return True
        return False
    
    def add_tag(self, name, user_login):
        # TODO: Maybe raise exception if this item already has such (tag, user_login)?
        assert user_login is not None
        tag = Tag(name)
        item_tag = Item_Tag(tag, user_login)
        self.item_tags.append(item_tag)
        
    def set_field_value(self, name, value, user_login):
        '''Changes field value if it exists, or creates new field and sets a value to it.'''
        assert user_login is not None
        
        itf = None
        for item_field in self.item_fields:
            if item_field.field.name == name and item_field.user_login == user_login: 
                itf = item_field
                break
                
        if itf is not None:
            itf.field_value = value
        else:
            field = Field(name)
            item_field = Item_Field(field, value, user_login)
            self.item_fields.append(item_field)
            
    def format_field_vals(self):
        s = ""
        for item_field in self.item_fields:
            s += item_field.field.name + ": " + item_field.field_value + os.linesep
        if s:
            s = s[0:-1]
        return s
        
    def format_tags(self):
        '''Возвращает строку, содержащую список всех тегов элемента.'''
        s = ""
        for item_tag in self.item_tags:
            s += item_tag.tag.name + " "
        if s:
            s = s[0:-1]
        return s
    
    def remove_tag(self, tag_name):
        #TODO: Maybe should pass userLogin to this fun?
        i = 0
        while i < len(self.item_tags):
            item_tag = self.item_tags[i]
            if item_tag.tag.name == tag_name:
                break
            i = i + 1
            
        if i < len(self.item_tags):
            #тег найден - удаляем
            self.item_tags.pop(i)
            return True
        else:
            return None

    def remove_field(self, field_name):
        #TODO: Maybe should pass userLogin to this fun?
        i = 0
        while i < len(self.item_fields):
            item_field = self.item_fields[i] 
            if item_field.field.name == field_name:
                break
            i = i + 1
            
        if i < len(self.item_fields):
            #тег найден - удаляем
            self.item_fields.pop(i)
            return True
        else:
            return None
        
    
    def has_tag(self, tag_name):
        '''Возвращает True, если данный элемент имеет тег с имененем tag_name.'''
        for item_tag in self.item_tags:
            if item_tag.tag.name == tag_name:
                return True
        return False
    
    def has_field(self, field_name, field_value=None):
        '''Возвращает True, если данный элемент имеет поле с имененем field_name.
        Если field_value не None, то проверяется еще и равно ли данное поле этому значению.'''
        for item_field in self.item_fields:
            if item_field.field.name == field_name:
                if field_value is None or item_field.field_value == str(field_value):
                    return True
        return False
        
    def check_valid(self):
        '''Проверяет, что состояние объекта допустимое. Связи с другими объектами не учитываются.'''
        if self.title == "" or self.title is None:
            raise Exception(tr("Attribute Item.title shouldn't be empty."))
        return True
    
    def is_data_ref_null(self):
        return self.data_ref is None
        
                
class DataRef(Base, memento.Serializable):
    '''
    Ссылка на файл или URL.
    '''
    
    FILE = "FILE"  
    URL = "URL" #TODO: URL type is deprecated. Do not use it anymore. User can always save an url for an item with a field
    
    __tablename__ = "data_refs"
    
    id = sqa.Column(sqa.Integer, primary_key=True)
    
    #Локатор ресурса. Для объектов типа 'FILE' это путь к файлу внутри хранилища
    #для объектов 'URL' --- это непосредственно url-ссылка
    url_raw = sqa.Column(sqa.String, name="url", nullable=False, unique=True)
    
    #TODO !!! Возможно имеет смысл для объектов типа FILE отдельно хранить путь и базовое имя файла.
    #Это может пригодиться для поиска файлов по его физическому имени (т.к. так как сейчас
    #если искать наподобие data_ref.url LIKE '%something%' то поиск будет выдавать совпадения,
    #если совпадает имя директории на пути к файлу.
    
    #Тип объекта DataRef
    #TODO Добавить тип ZIP (архив), а также можно добавить тип DIR (директория)
    type = sqa.Column(sqa.Enum(FILE, URL), nullable=False)
    
    #Хеш (md5 или sha1) от содержимого файла. Для объектов DataRef имеющих тип type отличный от 'FILE' равен NULL
    hash = sqa.Column(sqa.String)
    
    #Дата/время вычисления хеша hash. Если date_hashed < даты последней модификации физического файла, то хеш нужно пересчитать
    date_hashed = sqa.Column(sqa.DateTime)
    
    #Размер физического файла на диске (для объектов типа 'FILE', для остальных NULL)
    size = sqa.Column(sqa.Integer)
    
    #Это дата создания объекта DataRef в БД (не имеет ничего общего с датой создания файла на ФС)
    date_created = sqa.Column(sqa.DateTime)
    
    #Пользователь-владелец данного объекта (обычно тот, кто его создал)
    #deprecated because it's enough information in field Item.user_login
    user_login = sqa.Column(sqa.String, ForeignKey("users.login"))
    
    
    user = relationship(User, cascade="save-update, merge, expunge, refresh-expire")
    
    thumbnails = relationship("Thumbnail", cascade="all, delete-orphan")
    
    items = relationship("Item", cascade="expunge, refresh-expire")


    def __init__(self, type=None, url=None, date_created=None):
        self.type = type
        self.url = url
        
        if date_created is not None:
            self.date_created = date_created
        else:
            self.date_created = datetime.datetime.today()
        
        # This two fields is used only in function "Add many items recursively"
        # srcAbsPathToRecursionRoot is a absolute path to the root directory 
        # from where recursive scanning was started.
        self.srcAbsPathToRecursionRoot = None
        self.srcAbsPath = None
        
        # This is a relative path to file in repository (where you want to put it)
        # NOTE: This is not a path to directory!
        self.dstRelPath = None
    
    @orm.reconstructor
    def __init_on_load__(self):
        self.srcAbsPathToRecursionRoot = None
        self.srcAbsPath = None
        self.dstRelPath = None
    
    
    def toJson(self):
        return {"__class__": self.__class__.__name__,
                "__module__": "db_schema",
                "url": self.url_raw,
                "type": self.type,
                "hash": self.hash,
                "date_hashed": self.date_hashed,
                "size": self.size,
                "date_created": self.date_created,
                "user_login": self.user_login,
                }
        
    @staticmethod
    def fromJson(objState):
        dr = DataRef(type=objState["type"], 
                     url=objState["url"],
                     date_created=objState["date_created"])
        dr.hash = objState["hash"]
        dr.date_hashed = objState["date_hashed"]
        dr.size = objState["size"]
        dr.user_login = objState["user_login"]
        return dr
        
    
    def _get_url(self):
        if self.type == DataRef.FILE and self.url_raw is not None:
            return helpers.from_db_format(self.url_raw)
        else:
            return self.url_raw
        
    def _set_url(self, value):
        #Сохранять в БД этот url и  HistoryRec.url нужно всегда в формате Unix (т.е. с прямыми слешами)
        if self.type == DataRef.FILE and value is not None:
            value = helpers.to_db_format(value)
        self.url_raw = value
                
    url = property(_get_url, _set_url, doc="Свойство url.")
    
    @staticmethod
    def _sql_from():
        return '''
            data_refs.id AS data_refs_id, 
            data_refs.url AS data_refs_url, 
            data_refs.type AS data_refs_type, 
            data_refs.hash AS data_refs_hash, 
            data_refs.date_hashed AS data_refs_date_hashed, 
            data_refs.size AS data_refs_size, 
            data_refs.date_created AS data_refs_date_created, 
            data_refs.user_login AS data_refs_user_login '''

    
                
        
    def is_image(self):
        '''Возвращает True, если данный DataRef объект имеет тип FILE и ссылается
        на растровое графическое изображение, одного из поддерживаемых форматов.
        Проверка основана на сравнении расширения файла со списком расширений поддерживаемых
        форматов.'''
        supported = set([".bmp", ".gif", ".jpg", ".jpeg", ".png", ".pbm", ".pgm", ".ppm", ".xbm", ".xpm"])
        if self.type and self.type == "FILE" and not is_none_or_empty(self.url):
            
            root, ext = os.path.splitext(self.url.lower())
            if ext in supported:
                return True
        
        return False
            
        
    

class Thumbnail(Base):
    '''
    Миниатюра изображения графического файла, сама ссылка на файл хранится в DataRef.
    
    TODO: Кстати, миниатюры можно добавлять не только для графических файлов.
    Если DataRef указывает на книгу в формате pdf, то миниатюра может содержать 
    изображение титульного листа книги (причем не обязательно очень маленького разрешения).
    Для mp3 файла это может быть обложка диска альбома и т.п.
    '''
    __tablename__ = "thumbnails"
    
    data_ref_id = sqa.Column(sqa.Integer, ForeignKey("data_refs.id"), primary_key=True)
    
    #Размер в пикселях миниатюры (это величина наибольшей размерности)
    size = sqa.Column(sqa.Integer, primary_key=True)
    
    #Двоичные данные изображения миниатюры
    data = sqa.Column(sqa.LargeBinary)
    
    #Дата создания миниатюры
    #Если Thumbnail.date_created будет новее, чем DataRef.date_hashed, 
    #то это повод для обновления миниатюры
    date_created = sqa.Column(sqa.DateTime)
    
    #Логическое поле, определяющее, следует ли автоматически обновлять миниатюру
    #auto_updated = sqa.Column(sqa.Boolean, default=True)
        
    
    def __init__(self):
        self.data_ref_id = None
        self.size = None        
        self.data = None
        self.date_created = datetime.datetime.today()
        
    
    @staticmethod
    def _sql_from():
        return '''
        thumbnails.data_ref_id AS thumbnails_data_ref_id, 
        thumbnails.size AS thumbnails_size,
        thumbnails.data AS thumbnails_data, 
        thumbnails.date_created AS thumbnails_date_created '''
    
class Tag(Base):
    '''
    Тег (ключевое слово), описывающий элементы хранилища.
    '''
    __tablename__ = "tags"
    
    id = sqa.Column(sqa.Integer, primary_key=True)
    name = sqa.Column(sqa.String, nullable=False, unique=True)
    synonym_code = sqa.Column(sqa.Integer)

    def __init__(self, name=None):
        self.id = None
        self.name = name
        self.synonym_code = None
        
    @staticmethod
    def _sql_from():
        return '''
        tags.id as tags_id,
        tags.name as tags_name,
        tags.synonym_code as tags_synonym_code '''
        
class Item_Tag(Base):
    __tablename__ = "items_tags"
        
    item_id = sqa.Column(sqa.Integer, ForeignKey("items.id"), primary_key=True)
    tag_id = sqa.Column(sqa.Integer, ForeignKey("tags.id"), primary_key=True)
    user_login = sqa.Column(sqa.String, ForeignKey("users.login"), primary_key=True)
    
    #item = relationship(Item)
    tag = relationship(Tag, cascade="save-update, merge, expunge, refresh-expire")
    #user = relationship(User)
    
    def __init__(self, tag=None, user_login=None):
        self.tag = tag
        self.user_login = user_login
        if tag is not None:
            self.tag_id = tag.id            
        
    @staticmethod
    def _sql_from():
        return '''
        items_tags.item_id as items_tags_item_id, 
        items_tags.tag_id as items_tags_tag_id, 
        items_tags.user_login as items_tags_user_login '''
    
class Field(Base):
    '''
    Поле вида ключ=значение, описывающее элементы хранилища.
    '''
    __tablename__ = "fields"    
    
    id = sqa.Column(sqa.Integer, primary_key=True)
    name = sqa.Column(sqa.String, nullable=False, unique=True)
    synonym_code = sqa.Column(sqa.Integer)
    #value_type = sqa.Column(sqa.Enum("STRING", "NUMBER"), nullable=False, default="STRING")

    def __init__(self, name=None):
        self.id = None
        self.name = name
        self.synonym_code = None
    
    @staticmethod
    def _sql_from():
        return '''
        fields.id as fields_id,
        fields.name as fields_name,
        fields.synonym_code as fields_synonym_code '''
    

class Item_Field(Base):
    '''
    Значение поля, связанное с элементом хранилища.
    '''
    __tablename__ = "items_fields"
#    __table_args__ = (ForeignKeyConstraint(["field_name", "field_user_login"], ["fields.name", "fields.user_login"]),
#        {} #{} обязательно нужны, даже если внутри них - пусто
#        )
    
    item_id = sqa.Column(sqa.Integer, ForeignKey("items.id"), primary_key=True)
    field_id = sqa.Column(sqa.String, ForeignKey("fields.id"), primary_key=True)
    user_login = sqa.Column(sqa.String, ForeignKey("users.login"), primary_key=True)
    field_value = sqa.Column(sqa.String, nullable=False, default="")

    #item = relationship(Item)
    field = relationship(Field, cascade="save-update, merge, expunge, refresh-expire")
    #user = relationship(User)
    
    
    def __init__(self, field=None, value=None, user_login=None):
        self.field = field        
        if field is not None:
            self.field_id = field.id
        self.field_value = value
        self.user_login = user_login
                    
    @staticmethod
    def _sql_from():
        return '''
        items_fields.item_id as items_fields_item_id, 
        items_fields.field_id as items_fields_field_id, 
        items_fields.user_login as items_fields_user_login, 
        items_fields.field_value as items_fields_field_value '''
        
#TODO сделать классы для групп полей и тегов





