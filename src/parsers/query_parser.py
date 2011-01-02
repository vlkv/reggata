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
    FieldsConjunction, CompoundQuery
import ply.yacc as yacc
from parsers.query_tokens import *
from exceptions import YaccError


def p_query(p):
    '''query : simple_query
             | compound_query 
             | compound_query extra_clause
    '''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        for e in p[2]:
            p[1].add_extra_clause(e)            
        p[0] = p[1]
    else:
        raise ValueError(tr("len(p) has incorrect value."))
        

# Составное выражение, представляющее собой несколько SQL запросов, соединенных
# операциями INTERSECT, UNION, EXCEPT.
def p_compound_query(p):
    '''compound_query : LPAREN simple_query RPAREN'''
    p[0] = CompoundQuery(p[2])
    
def p_compound_query_and(p):
    '''compound_query : compound_query AND LPAREN simple_query RPAREN
                      | compound_query LPAREN simple_query RPAREN '''
    if len(p) == 6:        
        p[1].and_elem(p[4])
    elif len(p) == 5:
        p[1].and_elem(p[3])
    else:
        raise ValueError(tr("len(p) has incorrect value."))
    p[0] = p[1]

def p_compound_query_or(p):
    '''compound_query : compound_query OR LPAREN simple_query RPAREN ''' 
    p[1].or_elem(p[4])
    p[0] = p[1]

def p_compound_query_and_not(p):
    '''compound_query : compound_query AND NOT LPAREN simple_query RPAREN '''
    p[1].and_not_elem(p[5])
    p[0] = p[1]
    

#Простое выражение, для выполнения которого достаточно одного SQL запроса
def p_simple_query(p):
    '''simple_query : tags_conjunction
                    | tags_conjunction extra_clause 
                    | fields_conjunction
                    | fields_conjunction extra_clause 
    ''' 
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        for e in p[2]:
            p[1].add_extra_clause(e)
        p[0] = p[1]


#Выражения user:<логин> ограничивают выборку только по объектам ItemTag или ItemField
#Но никак не сравниваются с владельцами объектов Item или DataRef.
#Таким образом, если пользователь прикрепил свой тег к чужому Item-у, то он 
#будет его видеть в своих запросах. 
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
    
def p_extra_clause_title(p):
    '''extra_clause : TITLE COLON STRING extra_clause'''
    e = ExtraClause('TITLE', p[3])
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
    '''fields_conjunction : fields_conjunction field_op_value
                          | fields_conjunction AND field_op_value'''
    if len(p) == 3:
        p[1].add_field_op_val(p[2])
    elif len(p) == 4:
        p[1].add_field_op_val(p[3])
    p[0] = p[1]

def p_fields_conjunction_empty(p):
    '''fields_conjunction : field_op_value'''
    fc = FieldsConjunction()
    fc.add_field_op_val(p[1])
    p[0] = fc
    

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
    raise YaccError(tr("Syntax error in the query: {}").format(str(p)))


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
    (FieldA >= 10)
    '''
    
    data_3 = r'''
    (Log AND Tag) AND (Author = James Rating > 5)
    '''
    
    data = data_3
    
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


