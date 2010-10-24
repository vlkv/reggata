# -*- coding: utf-8 -*-
'''
Created on 11.10.2010

@author: vlkv
'''
import sqlalchemy as sqa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import ForeignKey, ForeignKeyConstraint
from helpers import tr
import datetime


Base = declarative_base()


class User(Base):
    '''
    Пользователь системы reggata.
    '''
    __tablename__ = "users"
    
    login = sqa.Column(sqa.String, primary_key=True)
    password = sqa.Column(sqa.String)
    group = sqa.Column(sqa.Enum("USER", "ADMIN"), nullable=False, default="USER")
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



class Item(Base):
    '''
    Элемент (запись, объект) хранилища.
    '''
    __tablename__ = "items"
    
    id = sqa.Column(sqa.Integer, primary_key=True)
    title = sqa.Column(sqa.String, nullable=False)
    notes = sqa.Column(sqa.String)
    user_login = sqa.Column(sqa.String, ForeignKey("users.login"))
    date_created = sqa.Column(sqa.DateTime)
    
    #пользователь-владелец данного элемента
    user = relationship(User)
    
    #список связанных файлов/ссылок_URL
    item_data_refs = relationship("Item_DataRef", order_by="Item_DataRef.order_by_key")
    
    #tags - список связанных тегов
    item_tags = relationship("Item_Tag")
    
    #field_vals - список связанных полей
    item_fields = relationship("Item_Field")

    def __init__(self, user_login=None, title=None, notes=None, date_created=None):
        self.user_login = user_login
        self.title = title
        self.notes = notes
        if date_created is not None:
            self.date_created = date_created
        else:
            self.date_created = datetime.datetime.today()
        
        
    def check_valid(self):
        '''Проверяет, что состояние объекта допустимое. Связи с другими объектами не учитываются.'''
        if self.title == "" or self.title is None:
            raise Exception(tr("Attribute Item.title shouldn't be empty."))
        return True
        
        

        
class DataRef(Base):
    '''
    Ссылка на файл или URL.
    '''
    __tablename__ = "data_refs"
    
    id = sqa.Column(sqa.Integer, primary_key=True)
    url = sqa.Column(sqa.String, nullable=False, unique=True)
    type = sqa.Column(sqa.Enum("FILE", "URL"), nullable=False)
    hash = sqa.Column(sqa.String)
    date_hashed = sqa.Column(sqa.DateTime)
    size = sqa.Column(sqa.Integer)
    date_created = sqa.Column(sqa.DateTime)
    user_login = sqa.Column(sqa.String, ForeignKey("users.login"))
    
    user = relationship(User)


    def __init__(self, url=None, date_created=None):
        self.url = url
        if date_created is not None:
            self.date_created = date_created
        else:
            self.date_created = datetime.datetime.today()
        


class Item_DataRef(Base):
    __tablename__ = "items_data_refs"
        
    item_id = sqa.Column(sqa.Integer, ForeignKey("items.id"), primary_key=True)
    data_ref_id = sqa.Column(sqa.Integer, ForeignKey("data_refs.id"), primary_key=True)
    user_login = sqa.Column(sqa.String, ForeignKey("users.login"), primary_key=True)
    order_by_key = sqa.Column(sqa.Integer)
    
    item = relationship(Item)
    data_ref = relationship("DataRef")
    user = relationship(User)
    
    def __init__(self, data_ref=None):
        self.data_ref = data_ref
        if data_ref is not None:
            self.data_ref_id = data_ref.id
            self.user_login = data_ref.user_login
        self.item_id = None
        self.order_by_key = None
             
        
    
        
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
        
class Item_Tag(Base):
    __tablename__ = "items_tags"
        
    item_id = sqa.Column(sqa.Integer, ForeignKey("items.id"), primary_key=True)
    tag_id = sqa.Column(sqa.Integer, ForeignKey("tags.id"), primary_key=True)
    user_login = sqa.Column(sqa.String, ForeignKey("users.login"), primary_key=True)
    
    item = relationship(Item)
    tag = relationship(Tag)
    user = relationship(User)
    
    def __init__(self, tag=None):        
        self.tag = tag
        if tag is not None:
            self.tag_id = tag.id            
            
        
    
class Field(Base):
    '''
    Поле вида ключ=значение, описывающее элементы хранилища.
    '''
    __tablename__ = "fields"    
    
    id = sqa.Column(sqa.Integer, primary_key=True)
    name = sqa.Column(sqa.String, nullable=False, unique=True)
    synonym_code = sqa.Column(sqa.Integer)
#    value_type = sqa.Column(sqa.Enum("STRING", "NUMBER"), nullable=False, default="STRING")

    def __init__(self, name=None):
        self.id = None
        self.name = name
        self.synonym_code = None
        
    

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

    item = relationship(Item)
    field = relationship(Field)
    user = relationship(User)
    
    
    def __init__(self, field=None, value=None, user_login=None):
        self.field = field        
        if field is not None:
            self.field_id = field.id
        self.field_value = value
        self.user_login = user_login
                    
        
#TODO сделать классы для групп полей и тегов





