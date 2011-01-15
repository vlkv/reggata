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
    FieldsConjunction, CompoundQuery, SingleExtraClause
import ply.yacc as yacc
from parsers.query_tokens import *
from exceptions import YaccError
import consts
import helpers
from parsers import query_tokens, query_tree_nodes

def p_query(p):
    '''query    : compound_query
    '''
    p[0] = p[1]
    
#def p_simple_query(p):
#    '''simple_query : tags_fields_conj
#    '''
##                    | tags_disj
##                    | fields_disj
#    p[0]

def p_compound_query(p):
    '''compound_query : compound_query OR tags_fields_conj
                      | tags_fields_conj
    '''
#                      | paren_simple_query and_not_or compound_query
    
    if len(p) == 2:
        tags_fields_conj = p[1]
        if tags_fields_conj[0].len() > 0:
            compound_query = query_tree_nodes.CompoundQuery(tags_fields_conj[0])
            if tags_fields_conj[1].len() > 0:
                compound_query.and_elem(tags_fields_conj[1])
        elif tags_fields_conj[1].len() > 0:
            compound_query = query_tree_nodes.CompoundQuery(tags_fields_conj[1])
        else:
            raise ValueError(helpers.tr("Error in p_compound_query()."))        
    elif len(p) == 4:
        tags_fields_conj = p[3]
        compound_query = p[1]
        if tags_fields_conj[0].len() > 0:
            compound_query.or_elem(tags_fields_conj[0])
            if tags_fields_conj[1].len() > 0:
                compound_query.and_elem(tags_fields_conj[1])
        elif tags_fields_conj[1].len() > 0:
            compound_query.or_elem(tags_fields_conj[1])
        else:
            raise ValueError(helpers.tr("Error in p_compound_query()."))
    else:
        raise YaccError(helpers.tr("Error in p_compound_query()."))
    p[0] = compound_query
        


#def p_paren_simple_query(p):
#    '''paren_simple_query  : LPAREN tags_fields_conj RPAREN
#                        | LPAREN tags_disj RPAREN
#                        | LPAREN fields_disj RPAREN
#    '''
#    p[0]

def p_and_not_or(p):
    '''and_not_or : AND
                  | OR
                  | NOT
    '''
    p[0] = p[1]

def p_tags_fields_conj(p):
    '''tags_fields_conj : tag_field
                        | tags_fields_conj tag_field
                        | tags_fields_conj AND tag_field
    '''
    if len(p) == 2:
        tag_field = p[1]
        if isinstance(tag_field, query_tree_nodes.Tag):
            tags_conj = query_tree_nodes.TagsConjunction()
            tags_conj.add_tag(tag_field)
            p[0] = (tags_conj, query_tree_nodes.FieldsConjunction())
        elif isinstance(tag_field, query_tree_nodes.FieldOpVal):
            fields_conj = query_tree_nodes.FieldsConjunction()
            fields_conj.add_field_op_val(tag_field)
            p[0] = (fields_conj, query_tree_nodes.TagsConjunction())
        else:
            raise TypeError(helpers.tr("Tag of Field instance expected."))
    elif len(p) in [3, 4]:
        if len(p) == 3:
            tags_fields_conj = p[1]
            tag_field = p[2]
        elif len(p) == 4:
            tags_fields_conj = p[1]
            tag_field = p[3]

        if isinstance(tag_field, query_tree_nodes.Tag):
            if isinstance(tags_fields_conj[0], query_tree_nodes.TagsConjunction):
                tags_fields_conj[0].add_tag(tag_field)
            else:
                tags_fields_conj[1].add_tag(tag_field)
        elif isinstance(tag_field, query_tree_nodes.FieldOpVal):
            if isinstance(tags_fields_conj[0], query_tree_nodes.FieldsConjunction):
                tags_fields_conj[0].add_field_op_val(tag_field)
            else:                
                tags_fields_conj[1].add_field_op_val(tag_field)
        else:
            raise TypeError(helpers.tr("Tag of Field instance expected."))
        p[0] = tags_fields_conj
    else:
        raise YaccError("Error in p_tags_fields_conj().")
        
        
        

def p_tag_field(p):
    '''tag_field : field_op_value
                 | tag_not_tag
    '''
    p[0] = p[1]



    

#def p_query(p):
#    '''query : simple_query
#             | compound_query 
#             | compound_query extra_clause
#    '''
#    if len(p) == 2:
#        p[0] = p[1]
#    elif len(p) == 3:
#        for e in p[2]:
#            p[1].add_extra_clause(e)            
#        p[0] = p[1]
#    else:
#        raise ValueError(helpers.tr("len(p) has incorrect value."))
        

## Составное выражение, представляющее собой несколько SQL запросов, соединенных
## операциями INTERSECT, UNION, EXCEPT.
#def p_compound_query(p):
#    '''compound_query : LPAREN simple_query RPAREN
#    '''
#    p[0] = CompoundQuery(p[2])
#    
#def p_compound_query_and(p):
#    '''compound_query : compound_query AND LPAREN simple_query RPAREN
#                      | compound_query LPAREN simple_query RPAREN
#    '''
#    if len(p) == 6:        
#        p[1].and_elem(p[4])
#    elif len(p) == 5:
#        p[1].and_elem(p[3])
#    else:
#        raise ValueError(helpers.tr("len(p) has incorrect value."))
#    p[0] = p[1]
#
#def p_compound_query_or(p):
#    '''compound_query : compound_query OR LPAREN simple_query RPAREN
#    ''' 
#    p[1].or_elem(p[4])
#    p[0] = p[1]
#
#def p_compound_query_and_not(p):
#    '''compound_query : compound_query AND NOT LPAREN simple_query RPAREN
#    '''
#    p[1].and_not_elem(p[5])
#    p[0] = p[1]
#    
#
##Простое выражение, для выполнения которого достаточно одного SQL запроса
#def p_simple_query(p):
#    '''simple_query : tags_conjunction
#                    | tags_conjunction extra_clause 
#                    | fields_conjunction
#                    | fields_conjunction extra_clause
#    ''' 
#    if len(p) == 2:
#        p[0] = p[1]
#    elif len(p) == 3:
#        for e in p[2]:
#            p[1].add_extra_clause(e)
#        p[0] = p[1]
#        
#def p_simple_query_single_extra_clause(p):
#    '''simple_query : extra_clause                    
#    ''' 
#    sec = SingleExtraClause()
#    for e in p[1]:
#        sec.add_extra_clause(e)
#        p[0] = sec
#    
#Выражения user:<логин> ограничивают выборку только по объектам ItemTag или ItemField
#Но никак не сравниваются с владельцами объектов Item или DataRef.
#Таким образом, если пользователь прикрепил свой тег к чужому Item-у, то он 
#будет его видеть в своих запросах. 
def p_extra_clause_user(p):
    '''extra_clause : USER COLON STRING extra_clause
    '''
    e = ExtraClause('USER', p[3])
    p[4].append(e)
    p[0] = p[4]

    
def p_extra_clause_path(p):
    '''extra_clause : PATH COLON STRING extra_clause
    '''
    e = ExtraClause('PATH', p[3])
    p[4].append(e)
    p[0] = p[4]
    
def p_extra_clause_title(p):
    '''extra_clause : TITLE COLON STRING extra_clause
    '''
    e = ExtraClause('TITLE', p[3])
    p[4].append(e)
    p[0] = p[4]
    
def p_extra_clause_empty(p):
    '''extra_clause : 
    '''    
    p[0] = []
    
    
## Конъюнкция имен тегов или их отрицаний
#def p_tags_conjunction(p):
#    '''tags_conjunction : tags_conjunction AND tag_not_tag
#                        | tags_conjunction tag_not_tag
#                        | tag_not_tag
#    '''
#    if len(p) == 4:
#        p[1].add_tag(p[3])
#        p[0] = p[1]
#    elif len(p) == 3:
#        p[1].add_tag(p[2])
#        p[0] = p[1]
#    elif len(p) == 2:
#        tc = TagsConjunction()
#        tc.add_tag(p[1])
#        p[0] =  tc

# Тег или его отрицание
def p_tag_not_tag(p):
    '''tag_not_tag : NOT tag_name
                   | tag_name
    '''
    if len(p) == 3:
        p[2].negate()
        p[0] = p[2]
    elif len(p) == 2:
        p[0] = p[1]

def p_tag_name(p):
    'tag_name : STRING'
    p[0] = Tag(p[1])
    
#    
#def p_fields_conjunction(p):
#    '''fields_conjunction : fields_conjunction field_op_value
#                          | fields_conjunction AND field_op_value
#    '''
#    if len(p) == 3:
#        p[1].add_field_op_val(p[2])
#    elif len(p) == 4:
#        p[1].add_field_op_val(p[3])
#    p[0] = p[1]
#
#def p_fields_conjunction_empty(p):
#    '''fields_conjunction : field_op_value
#    '''
#    fc = FieldsConjunction()
#    fc.add_field_op_val(p[1])
#    p[0] = fc
#    

def p_field_op_value(p):
    '''field_op_value : field_name field_op field_value 
    '''
    p[0] = FieldOpVal(p[1], p[2], p[3])
    
def p_field_name(p):
    '''field_name : STRING 
    '''
    p[0] = p[1]
    
def p_field_op(p):
    '''field_op : EQUAL
                | GREATER
                | GREATER_EQ
                | LESS
                | LESS_EQ
                | LIKE  
    '''
    p[0] = p[1]

def p_field_value(p):
    '''field_value : STRING 
    '''
    p[0] = p[1]
    

# Error rule for syntax errors
def p_error(p):
    raise YaccError(helpers.tr("Syntax error in the query: {}").format(str(p)))


#Строим лексический анализатор
lexer = build_lexer()

#Строим синтаксический анализатор
parser = yacc.yacc(errorlog=consts.yacc_errorlog)

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
    
    data_4 = r'''
    Log AND Tag OR Author = James AND Good
    '''
    
    data = data_4
    
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


