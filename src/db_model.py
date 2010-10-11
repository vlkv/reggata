'''
Created on 11.10.2010

@author: vlkv
'''
import sqlalchemy as sqa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import ForeignKey


Base = declarative_base()
#metadata = sqa.MetaData()
metadata = Base.metadata



class User(Base):
    '''
    Пользователь системы reggata
    '''
    __tablename__ = "users"
    
    login = sqa.Column(sqa.String, primary_key=True)
    name = sqa.Column(sqa.String)
    password = sqa.Column(sqa.String)
    notes = sqa.Column(sqa.String)
    group = sqa.Enum("USER", "ADMIN", nullable=False, default="USER")
    
    def __init__(self):
        '''
        Constructor
        '''



#Таблица связей Tag и Item
tags_items = sqa.Table('tags_items', metadata,
                   sqa.Column('item_id', sqa.Integer, ForeignKey('items.id')), 
                   sqa.Column('tag_name', sqa.String, ForeignKey('tags.name')),
                   sqa.Column('tag_user_login', sqa.String, ForeignKey('tags.user_login')))




class Item(Base):
    '''
    Элемент (запись, объект) хранилища
    '''
    __tablename__ = "items"
    
    id = sqa.Column(sqa.Integer, primary_key=True)
    title = sqa.Column(sqa.String, nullable=False)
    notes = sqa.Column(sqa.String)
    user_login = sqa.Column(sqa.String, ForeignKey("users.login"))
    
    #пользователь-владелец данного элемента
    user = relationship(User, backref=backref("items"))
    
    #список связанных файлов/ссылок URL
    data_refs = relationship("DataRef", order_by="DataRef.order_by_key", backref=backref("item"))
    
    #tags - список связанных тегов
    tags = relationship("Tag", secondary=tags_items, backref='items')
    
    #fvals - список связанных полей

    def __init__(self):
        '''
        Constructor
        '''
        
        
        
        
class DataRef(Base):
    '''
    Ссылка на файл или URL
    '''
    __tablename__ = "data_refs"
    
    url = sqa.Column(sqa.String, primary_key=True)
    hash = sqa.Column(sqa.String)
    hash_date = sqa.Column(sqa.DateTime)
    size = sqa.Column(sqa.Integer, nullable=False, default=0)
    order_by_key = sqa.Column(sqa.Integer)
    item_id = sqa.Column(sqa.Integer, ForeignKey("items.id"))
    user_login = sqa.Column(sqa.String, ForeignKey("users.login"))
    
    item = relationship(Item, backref=backref("data_refs"))
    user = relationship(User)

    def __init__(self):
        '''
        Constructor
        '''
        
        
        
        
class Tag(Base):
    '''
    Тег, описывающий элементы хранилища
    '''
    __tablename__ = "tags"
    
    name = sqa.Column(sqa.String, primary_key=True)
    user_login = sqa.Column(sqa.String, ForeignKey("users.login"), primary_key=True)
    
    #Пользователь, кто создал данный тег
    user = relationship(User, backref=backref("tags"))

    def __init__(self):
        '''
        Constructor
        '''
        
