'''
Created on 24.10.2010

@author: vlkv
'''

import ply.lex as lex
import helpers
from helpers import tr
import re

#Зарезервированные слова и соответствующие им типы токенов
reserved = {
   'И' : 'AND',
   'ИЛИ' : 'OR',
   'НЕ' : 'NOT',
   'user' : 'USER',
   'path' : 'PATH',   
}

#Список типов токенов
tokens = [
   'STRING', #Строка, которая либо отдельное слово, либо в двойных кавычках все что угодно
   'LPAREN', #Открывающая круглая скобка ) 
   'RPAREN', #Закрывающая круглая скобка )
   'COLON', #Двоеточие : (ставится после ключевых слов user и после path)
   
] + list(reserved.values())

#Строка в двойных кавычках, которая может содержать две escape последовательности:
# 1) \" для отображения кавычки "
# 2) \\ для отображения слеша \
def t_STRING(t):
    r'"(\\["\\]|[^"\\])*" | [\w]+'
    t.type = reserved.get(t.value, 'STRING')    
    if t.type == 'STRING' and t.value.startswith('"') and t.value.endswith('"'):
        t.value = t.value.replace(r"\\", "\\") #Заменяем \\ на \
        t.value = t.value.replace(r'\"', r'"') #Заменяем \" на "
        t.value = t.value[1:-1] #Удаляем кавычки с начала и с конца, "abc" становится abc        
    return t

t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_COLON = r':'


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
        and i.id NOT IN (select i.id from items i 
        left join items_tags it on i.id = it.item_id 
        left join tags t on t.id = it.tag_id
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
        
        
        s = '''select distinct i.id, i.title, i.notes, i.user_login 
        from items i 
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
    '''extras : extras USER COLON STRING '''
    e = Extras()
    e.type = 'USER'
    e.value = p[4]
    if type(p[1]) == list:
        p[1].append(e)
    else:
        p[1] = [e]        
    p[0] = p[1]

    
def p_extras_path(p):
    '''extras : extras PATH COLON STRING '''
    e = Extras()
    e.type = 'PATH'
    e.value = p[4]
    if type(p[1]) == list:
        p[1].append(e)
    else:
        p[1] = [e]        
    p[0] = p[1]
    
def p_extras_one_user(p):
    '''extras : USER COLON STRING'''
    e = Extras()
    e.type = 'USER'
    e.value = p[3]
    p[0] = [e]
    
def p_extras_one_path(p):
    '''extras : PATH COLON STRING'''
    e = Extras()
    e.type = 'PATH'
    e.value = p[3]
    p[0] = [e]
    

def p_tags_conjunction_1(p):
    '''tags_conjunction : tags_conjunction AND tag_not_tag'''
    p[1].add_tag(p[3])
    p[0] = p[1]
    
def p_tags_conjunction_2(p):
    'tags_conjunction : tag_not_tag'
    exp = TagsConjunction()
    exp.add_tag(p[1])
    p[0] =  exp
    
def p_tag_not_tag_1(p):
    'tag_not_tag : NOT tag'
    p[2].negate()
    p[0] = p[2]
    
def p_tag_not_tag_2(p):
    'tag_not_tag : tag'
    p[0] = p[1]

def p_tag(p):
    'tag : STRING'
    p[0] = Tag(p[1])

# Error rule for syntax errors
def p_error(p):
    print("Syntax error in input! " + str(p))





# Build the lexer
lexer = lex.lex()

# Build the parser
parser = yacc.yacc()



if __name__ == '__main__':
##############################
    # Test data
    data = r'''
   Tag1 И НЕ "Слеш\\ кавычка\" конец" И "Тег 2" user : "asdf"
    '''
    
##############################    
    lexer.input(data)
    
    # Tokenize
    while True:
        tok = lexer.token()
        if not tok: break      # No more input
        print(tok)
##############################    
    result = parser.parse(data)
    print(result.interpret())





