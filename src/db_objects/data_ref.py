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

Base = declarative_base()

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
    
    item = sqa.relationship(Item, backref=backref("data_refs", order_by=order_by_key))
    user = sqa.relationship(User)

    def __init__(self):
        '''
        Constructor
        '''
        