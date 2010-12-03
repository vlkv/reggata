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

Created on 27.11.2010

Это будет парсер для списка тегов, встречающийся на диалоге ItemDialog.
'''

import ply.yacc as yacc
from parsers.tags_def_tokens import *



#Далее следуют продукции грамматики языка 

def p_tags_def_expression(p):
    '''tags_def_expression : tags_def_expression tag '''
    p[1].append(p[2])
    p[0] = p[1]
    
def p_tags_def_expression_empty(p):
    '''tags_def_expression : '''
    p[0] = []

def p_tag(p):
    '''tag : STRING'''
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
    грамматики языка определения списка тегов. Возвращает список тегов, имена
    которых уже не содержат никаких escape-последовательностей.'''
    return parser.parse(text, lexer=lexer)


if __name__ == '__main__':
    
    text = r'Hip-hop "Hip-hop"  "quoted" "symbol \"a\" "'
    res = parse(text)
    print(res)
    for r in res:
        print(r)
        
        