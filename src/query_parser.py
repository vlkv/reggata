'''
Created on 24.10.2010

@author: vlkv
'''

class QueryParser(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''


class QueryExp(object):
    '''
    Абстрактный базовый класс для представления выражения или его любой части.
    Все классы будут от него наследоваться. 
    '''    

class SimpleExp(QueryExp):
    '''Простое_выр'''

class CompoundExp(QueryExp):
    '''Составное_выр'''
    pass
    
class MainCond(SimpleExp):
    '''Осн_условие'''
    pass

class TwoConds(SimpleExp):
    '''Два_условия'''
    main_cond = None
    extr_cond = None
    
class ExtrCond(QueryExp):
    '''Доп_условие'''
    pass

class UsersCond(ExtrCond):    
    extr_cond = None
    user_cond = None
    
class UserCond(ExtrCond):
    user_login = None
        