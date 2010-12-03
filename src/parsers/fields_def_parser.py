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

Created on 28.11.2010

Парсер списка пар <поле:значение>.
'''

import ply.yacc as yacc
from parsers.fields_def_tokens import *

#Далее следуют продукции грамматики языка 

def p_fields_def_expression(p):
    '''fields_def_expression : fields_def_expression field_value_pair '''
    p[1].append(p[2])
    p[0] = p[1]

def p_fields_def_expression_empty(p):
    '''fields_def_expression : '''
    p[0] = []

def p_field_value_pair(p):
    '''field_value_pair : field COLON value '''
    p[0] = (p[1], p[3])
    
def p_field(p):
    '''field : STRING'''
    p[0] = p[1]
    
def p_value(p):
    '''value : STRING'''
    p[0] = p[1]

#Правило для определения действий в случае возникновения ошибки
def p_error(p):
    print("Syntax error in input! " + str(p))

#Строим лексический анализатор
lexer = build_lexer()

#Строим синтаксический анализатор
parser = yacc.yacc()

def parse(text):
    '''Функция обертка, для удобства. Выполняет разбор строки text по правилам 
    грамматики языка определения списка пар поле:значение. Возвращает список кортежей
    вида (имя_поля, значение_поля), где имя_поля и значение_поля не содержат никаких 
    escape-последовательностей.'''
    return parser.parse(text, lexer=lexer)


if __name__ == '__main__':
    
    
    data = r'''
    Tag1 : "Slash\\:quote\" end" 
    and:"tag 2"
     user : "asdf"
    '''
    lexer.input(data)
    while True:
        tok = lexer.token()
        if not tok: break      # No more input
        print(tok)
    
    
#    text = r'asdf:asdf "asdf a":"sdf"'
    res = parse(data)
    print(res)
    for r in res:
        print(r)
        