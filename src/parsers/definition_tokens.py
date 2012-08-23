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

Tokens for parser from definition_parser module.
'''

from ply import lex
import re
import consts
from errors import LexError

#Список типов токенов
tokens = [
   'STRING', #Строка, которая либо отдельное слово, либо в двойных кавычках все что угодно
   'COLON',  #Символ-разделитель между именем поля и значением
]


# Строка. Iспользуется для представления имен тегов и полей, а также значений 
# полей и в нек. других случаях тоже...
def t_STRING(t):
    r'"(\\["\\]|[^"\\])*"|([^\s():=><~"\\])+' #Тут пробелы лишние нельзя ставить!!!
    # Объяснение данного регулярного выражения:
    # Первая часть: "(\\["\\]|[^"\\])*" Строкой может быть последовательность символов в двойных кавычках, 
    # состоящая из escaped " и \ (т.е. \" и \\) и не содержащая просто " и \
    # Вторая часть: ([^\s():=><~"\\])+ Строкой также может быть ненулевая последовательность символов,
    # не заключенная в кавычки и не содержащая пробельные символы, скобки, двоеточие, знаки 
    # больше меньше равно, тильда, " и обратный слеш \ (т.е. не содержит служебные символы языка)  
    
    if t.type == 'STRING' and t.value.startswith('"') and t.value.endswith('"') and not t.value.endswith(r'\"'):
        t.value = t.value.replace(r"\\", "\\") #Заменяем \\ на \
        t.value = t.value.replace(r'\"', r'"') #Заменяем \" на "
        t.value = t.value[1:-1] #Удаляем кавычки с начала и с конца, "abc" становится abc        
    return t

t_COLON = r':'

# Строка, содержащая игнорируемые символы (пробелы, табы и проч.)
t_ignore  = ' \t\n\r'

# Что делать, если возникнет ошибка
def t_error(t):
    raise LexError("Lexical error in '{}'".format(t.value[0]))


def build_lexer():
    '''Строит лексический анализатор на основе всех определенных здесь токенов.'''
    lexer = lex.lex(errorlog=consts.lex_errorlog)
    return lexer


def needs_quote(string):
    '''Возвращает True, если строку string нужно заключить в кавычки, чтобы она
    правильно была распознана как токен типа 'STRING'. 
    Это вспомогательная функция, не влияющая на работу парсера.'''
    
    #Если внутри строки есть пробелы
    if re.search(r'\s', string): #re.search() возвращает None если ничего не найдено
        return True
    
    #Если не подходит под регэксп токена STRING
    m = re.match(t_STRING.__doc__, string)
    if m is None or m.group() != string:
        return True
    
    return False



if __name__ == '__main__':
    
    
    data = r'''
    Tag1 : "Slash\\:quote\" end" 
    and:"tag 2"
    user : "asdf"
    '''
    lexer = build_lexer()
    lexer.input(data)
    while True:
        tok = lexer.token()
        if not tok: break      # No more input
        print(tok)
        
        
        
