'''
Created on 10.10.2010

@author: vlkv
'''
import sqlalchemy as sqa
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

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
        
        
#if __name__ == '__main__':    
#    engine = sqa.create_engine('sqlite:///mydata.db')
#    Base.metadata.create_all(engine)