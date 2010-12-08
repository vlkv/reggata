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

@author: vlkv
'''


from parsers.query_tree_nodes import TagsConjunction, Tag, Extras


import ply.yacc as yacc
from parsers.query_tokens import *

#Далее следуют продукции грамматики языка запросов 

def p_query_expression(p):
    '''query_expression : simple_expression
                        | compound_expression'''
    p[0] = p[1]
                    
def p_compound_expression(p):
    '''compound_expression : LPAREN simple_expression RPAREN'''
    p[0] = p[2]

#Простое выражение, для выполнения которого достаточно одного SQL запроса
def p_simple_expression(p):
    '''simple_expression : tags_conjunction
                         | tags_conjunction extras'''
    if len(p) == 2:        
        p[0] = p[1]
    elif len(p) == 3:
        for e in p[2]:
            p[1].add_extras(e)
        p[0] = p[1]

#Выражения user:<логин> ограничивают выборку только по объектам ItemTag или ItemField
#Но никак не сравниваются с владельцами объектов Item или DataRef.
#Таким образом, если пользователь прикрепил свой тег к чужому Item-у, то он 
#будет его видеть в своих запросах. 
def p_extras_user(p):
    '''extras : USER COLON STRING extras'''
    e = Extras('USER', p[3])
    p[4].append(e)
    p[0] = p[4]

    
def p_extras_path(p):
    '''extras : PATH COLON STRING extras'''
    e = Extras('PATH', p[3])
    p[4].append(e)
    p[0] = p[4]
    
def p_extras_empty(p):
    '''extras : '''    
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
    data = r'''
    Tag1 "Slash\\ quote\" end" and "tag 2" user : "asdf"
    '''
    
##############################
        
    lexer.input(data)
    
    # Tokenize
    while True:
        tok = lexer.token()
        if not tok: break      # No more input
        print(tok)
##############################    
#    result = parser.parse(data)
#    print(result.interpret())


#    print(need_quote("abc"))
#    
#    print(need_quote("abc:"))
#    
#    print(need_quote("andk"))
#    
#    print(need_quote("a nd"))


