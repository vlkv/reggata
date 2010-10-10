'''
Created on 10.10.2010

@author: vlkv
'''
import sqlalchemy as sqa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import ForeignKey
from user import User
from item import Item
from data_ref import DataRef

Base = declarative_base()

class Tag(Base):
    '''
    Тег, описывающий элементы хранилища
    '''
    __tablename__ = "tags"
    
    name = sqa.Column(sqa.String, primary_key=True)
    user_login = sqa.Column(sqa.String, ForeignKey("users.login"))
    
    #Пользователь, кто создал данный тег
    user = sqa.relationship(User)

    def __init__(self):
        '''
        Constructor
        '''
        