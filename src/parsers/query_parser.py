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

Created on 24.10.2010

Модуль содержит продукции грамматики языка запросов.
'''


from parsers.query_tree_nodes import TagsConjunction, Tag, ExtraClause, FieldOpVal,\
    FieldsConjunction


import ply.yacc as yacc
from parsers.query_tokens import *

 

def p_query(p):
    '''query : simple_query
             | compound_query '''
    p[0] = p[1]

def p_compound_query(p):
    '''compound_query : LPAREN simple_query RPAREN'''
    p[0] = p[2]
    
def p_compound_query_1(p):
    '''compound_query : LPAREN simple_query RPAREN AND compound_query
                           | LPAREN simple_query RPAREN OR compound_query 
                           | LPAREN simple_query RPAREN AND NOT compound_query '''
    if len(p) == 6:
        p[0] = p[2]
        #TODO...

#Простое выражение, для выполнения которого достаточно одного SQL запроса
def p_simple_query(p):
    '''simple_query : tags_conjunction
                         | tags_conjunction extra_clause
                         | fields_conjunction '''
    if len(p) == 2:        
        p[0] = p[1]
    elif len(p) == 3:
        for e in p[2]:
            p[1].add_extra_clause(e)
        p[0] = p[1]

def p_extra_clause_user(p):
    '''extra_clause : USER COLON STRING extra_clause'''
    e = ExtraClause('USER', p[3])
    p[4].append(e)
    p[0] = p[4]

    
def p_extra_clause_path(p):
    '''extra_clause : PATH COLON STRING extra_clause'''
    e = ExtraClause('PATH', p[3])
    p[4].append(e)
    p[0] = p[4]
    
def p_extra_clause_empty(p):
    '''extra_clause : '''    
    p[0] = []
    
    
# Конъюнкция имен тегов или их отрицаний
def p_tags_conjunction(p):
    '''tags_conjunction : tags_conjunction AND tag_not_tag
                        | tags_conjunction tag_not_tag
                        | tag_not_tag'''
    if len(p) == 4:
        p[1].add_tag(p[3])
        p[0] = p[1]
    elif len(p) == 3:
        p[1].add_tag(p[2])
        p[0] = p[1]
    elif len(p) == 2:
        tc = TagsConjunction()
        tc.add_tag(p[1])
        p[0] =  tc

# Тег или его отрицание
def p_tag_not_tag(p):
    '''tag_not_tag : NOT tag
                   | tag'''
    if len(p) == 3:
        p[2].negate()
        p[0] = p[2]
    elif len(p) == 2:
        p[0] = p[1]

def p_tag(p):
    'tag : STRING'
    p[0] = Tag(p[1])
    
    
def p_fields_conjunction(p):
    '''fields_conjunction : field_op_value fields_conjunction
                          | field_op_value AND fields_conjunction '''
    if len(p) == 3:
        p[2].add_field_op_val(p[1])
        p[0] = p[2]
    elif len(p) == 4:
        p[3].add_field_op_val(p[1])
        p[0] = p[3]

def p_fields_conjunction_empty(p):
    '''fields_conjunction : '''
    p[0] = FieldsConjunction()

def p_field_op_value(p):
    '''field_op_value : field_name field_op field_value '''
    p[0] = FieldOpVal(p[1], p[2], p[3])
    
def p_field_name(p):
    '''field_name : STRING '''
    p[0] = p[1]
    
def p_field_op(p):
    '''field_op : EQUAL
                | GREATER
                | GREATER_EQ
                | LESS
                | LESS_EQ
                | LIKE  '''
    p[0] = p[1]

def p_field_value(p):
    '''field_value : STRING '''
    p[0] = p[1]
    

# Error rule for syntax errors
def p_error(p):
    print("Syntax error in the query! " + str(p))


#Строим лексический анализатор
lexer = build_lexer()

#Строим синтаксический анализатор
parser = yacc.yacc()

def parse(text):
    '''Функция обертка, для удобства. Выполняет разбор строки text по правилам 
    грамматики языка запросов. Возвращает дерево разбора (корневой узел).'''
    return parser.parse(text, lexer=lexer)


if __name__ == '__main__':
##############################
    # Test data
    data_0 = r'''
    Tag1 "Slash\\ quote\" end" and "tag 2" user : "asdf"
    '''
    
    data_1 = r'''
    FieldA >= 10 FieldB~2010% and some = sdfsdf
    '''
    
    data_2 = r'''
    FieldA >= 10
    '''
    
    data = data_2
    
##############################
        
    lexer.input(data)
        
    while True:
        tok = lexer.token()
        if not tok: break      # No more input
        print(tok)
##############################
    result = parser.parse(data)
    print(result.interpret())


#    print(need_quote("abc"))
#    
#    print(need_quote("abc:"))
#    
#    print(need_quote("andk"))
#    
#    print(need_quote("a nd"))


