'''
Created on 10.10.2010

@author: vlkv
'''
import sqlalchemy as sqa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import ForeignKey
from user import User
from data_ref import DataRef
from tag import Tag


Base = declarative_base()

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
    user = sqa.relationship(User, backref=backref("items"))
    
    #список связанных файлов/ссылок URL
    data_refs = sqa.relationship(DataRef, order_by=DataRef.order_by_key, backref=backref("item"))
    
    #tags - список связанных тегов
    tags = sqa.relationship(Tag, backref=backref("items"))
    
    #fvals - список связанных полей

    def __init__(self):
        '''
        Constructor
        '''
        