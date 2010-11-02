'''
Created on 24.10.2010

@author: vlkv
'''

import ply.lex as lex
import helpers
from helpers import tr

#Зарезервированные слова и соответствующие им типы токенов
reserved = {
   'И' : 'AND',
   'ИЛИ' : 'OR',
   'НЕ' : 'NOT',
   'user:' : 'USER',
   'path:' : 'PATH',   
}

#Список типов токенов
tokens = [
   'NAME', #Имя тега или поля
   'LPAREN', 
   'RPAREN',
] + list(reserved.values())

def t_NAME(t):
    r'[\w:]+'
    t.type = reserved.get(t.value, 'NAME')
    return t

t_LPAREN  = r'\('
t_RPAREN  = r'\)'


# A string containing ignored characters (spaces and tabs)
t_ignore  = ' \t\n\r'

# Error handling rule
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1) #Пропускаем текущий символ и переходим к следующему


class QueryExpression(object):
    '''Базовый класс для всех классов-узлов синтаксического дерева разбора.'''
    def interpret(self):
        raise NotImplementedError(tr('This is an abstract method.'))


class Tag(QueryExpression):
    '''Узел синтаксического дерева для представления Тегов.'''
    name = None
    is_negative = None
    
    def __init__(self, name, is_negative=False):
        self.name = name
        self.is_negative = is_negative
    
    def negate(self):
        self.is_negative = not self.is_negative
        
    def interpret(self):
        return self.name
    
    def __str__(self):
        return self.name

class TagsConjunction(QueryExpression):
    '''
    Конъюнкция тегов или их отрицаний, например:
    Тег1 И Тег2 И НЕ Тег3
    
    SQL запрос:
    
    select * from items i 
    left join items_tags it on i.id = it.item_id
    left join tags t on t.id = it.tag_id
    where
        (t.name='Книга' or t.name='Программирование')
        and i.id NOT IN (select i.id from items i left join items_tags it on i.id = it.item_id left join tags t on t.id = it.tag_id
        where t.name='Проектирование')
    group by i.id 
    having count(*)=2
    '''
    yes_tags = []
    no_tags = []
    
    #Список дополнительных условий USER и PATH
    extras_paths = []
    extras_users = []
    
    @property
    def tags(self):
        return self.yes_tags + self.no_tags
    
    def add_tag(self, tag):
        if tag.is_negative:
            self.no_tags.append(tag)
        else:
            self.yes_tags.append(tag)
            
    def add_extras(self, ext):
        if ext.type == 'USER':
            self.extras_users.append(ext)
        elif ext.type == 'PATH':
            self.extras_paths.append(ext)
        else:
            raise Exception(tr("Unexpected type of extras {}").format(str(ext.type)))
            
    def interpret(self):
        group_by_having = ""
        if len(self.yes_tags) > 0:            
            yes_tags_str = "(" + helpers.to_commalist(self.yes_tags, lambda x: "t.name='" + x.interpret() + "'", ' or ') + ")"
            
            if len(self.yes_tags) > 1:
                group_by_having = '''group by i.id having count(*)={} '''.format(len(self.yes_tags))            
        else:
            yes_tags_str = " 1 "
            
        
        if len(self.extras_users) > 0:
            extras_users_str = "and (it.user_login IN (" + helpers.to_commalist(self.extras_users, lambda x: "'" + x.interpret() + "'", ", ") + ")) "
        else:
            extras_users_str = ""
        
        if len(self.no_tags) > 0:    
            no_tags_str = ''' and i.id NOT IN (select i.id from items i  
            left join items_tags it on i.id = it.item_id  
            left join tags t on t.id = it.tag_id 
            where (''' + helpers.to_commalist(self.no_tags, lambda x: "t.name='" + x.interpret() + "'", ' or ') + ''')
            ''' + extras_users_str + ") "
        else:
            no_tags_str = "" 
        
        
        s = '''select * from items i 
        left join items_tags it on i.id = it.item_id 
        left join tags t on t.id = it.tag_id 
            where ''' + yes_tags_str + ''' 
            ''' + extras_users_str + '''
            ''' + no_tags_str + '''
            ''' + group_by_having
                 
        #TODO сделать интерпретацию для токенов PATH            
            
        return s
        
class Extras(QueryExpression):
    type = None
    value = None
    
    def interpret(self):
        return str(self.value)


import ply.yacc as yacc

def p_query_expression(p):
    '''query_expression : simple_expression
                        | compound_expression'''
    p[0] = p[1]
                     
def p_empty(p):
    'empty :'
    pass

def p_compound_expression(p):
    '''compound_expression : LPAREN simple_expression RPAREN'''
    p[0] = p[2]
    
def p_simple_expression_1(p):
    '''simple_expression : tags_conjunction'''
    p[0] = p[1]
    
def p_simple_expression(p):
    '''simple_expression : tags_conjunction extras'''
    for e in p[2]:
        p[1].add_extras(e)
    p[0] = p[1]

def p_extras_user(p):
    '''extras : extras USER NAME '''
    e = Extras()
    e.type = 'USER'
    e.value = p[3]
    if type(p[1]) == list:
        p[1].append(e)
    else:
        p[1] = [e]        
    p[0] = p[1]

    
def p_extras_path(p):
    '''extras : extras PATH NAME '''
    e = Extras()
    e.type = 'PATH'
    e.value = p[3]
    if type(p[1]) == list:
        p[1].append(e)
    else:
        p[1] = [e]        
    p[0] = p[1]
    
def p_extras_one_user(p):
    '''extras : USER NAME'''
    e = Extras()
    e.type = 'USER'
    e.value = p[2]
    p[0] = [e]
    
def p_extras_one_path(p):
    '''extras : PATH NAME'''
    e = Extras()
    e.type = 'PATH'
    e.value = p[2]
    p[0] = [e]
    

def p_tags_conjunction_1(p):
    '''tags_conjunction : tags_conjunction AND tag'''
    p[1].add_tag(p[3])
    p[0] = p[1]
    
def p_tags_conjunction_2(p): 
    'tags_conjunction : tag'
    exp = TagsConjunction()
    exp.add_tag(p[1])
    p[0] =  exp
    
def p_tag_not(p):
    'tag : NOT NAME'
    t = Tag(p[2], is_negative=True)
    p[0] = t
    
def p_tag_yes(p):
    'tag : NAME'
    p[0] = Tag(p[1])

# Error rule for syntax errors
def p_error(p):
    print("Syntax error in input! " + str(p))

if __name__ == '__main__':
    
##############################
    # Test data
    data = '''
   ( Tag1 И НЕ Тег2 И Тег3 user: vlkv    user: lena )
    '''
##############################
    # Build the lexer
    lexer = lex.lex()
    lexer.input(data)
    
    # Tokenize
    while True:
        tok = lexer.token()
        if not tok: break      # No more input
        print(tok)
##############################
    # Build the parser
    parser = yacc.yacc()
    result = parser.parse(data)
    print(result.interpret())
    
    







