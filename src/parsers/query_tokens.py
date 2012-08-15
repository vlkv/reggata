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

Module contains a lexical analyzer of reggata query language.
'''
import ply.lex as lex
import re
from exceptions import LexError
import consts
from PyQt4.QtCore import QCoreApplication


AND_OPERATOR = QCoreApplication.translate("parsers", 'and', None, QCoreApplication.UnicodeUTF8)
OR_OPERATOR = QCoreApplication.translate("parsers", 'or', None, QCoreApplication.UnicodeUTF8)
NOT_OPERATOR = QCoreApplication.translate("parsers", 'not', None, QCoreApplication.UnicodeUTF8)
USER_KEYWORD = QCoreApplication.translate("parsers", 'user', None, QCoreApplication.UnicodeUTF8)
PATH_KEYWORD = QCoreApplication.translate("parsers", 'path', None, QCoreApplication.UnicodeUTF8)
TITLE_KEYWORD = QCoreApplication.translate("parsers", 'title', None, QCoreApplication.UnicodeUTF8)

#Зарезервированные слова и соответствующие им типы токенов
#Я хочу, чтобы операции and, or, not и др. были в нескольких вариантах.
#Например, чтобы and можно было записать как and, And, AND
#В словаре reserved: ключ - это зарезервированное слово, а значение - это тип токена
reserved = dict()
for keyword, type in [(AND_OPERATOR, 'AND'), (OR_OPERATOR, 'OR'), (NOT_OPERATOR, 'NOT'), 
              (USER_KEYWORD, 'USER'), (PATH_KEYWORD, 'PATH'), (TITLE_KEYWORD, 'TITLE')]:
    reserved[keyword.capitalize()] = type
    reserved[keyword.upper()] = type
    reserved[keyword.lower()] = type
#NOTE: ply displays a warning that token AND (OR and others) are defined more than once...


#Типы токенов
tokens = [
   'STRING', #Строка, которая либо отдельное слово, либо в двойных кавычках все что угодно
   'LPAREN', #Открывающая круглая скобка )
   'RPAREN', #Закрывающая круглая скобка )
   'COLON', #Двоеточие : (ставится после ключевых слов user и после path)
   
   #Операции, которые могут быть между именем поля и его значением:
   'EQUAL',
   'GREATER',
   'GREATER_EQ',
   'LESS',
   'LESS_EQ',
   'LIKE',
] + list(reserved.values())



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
    
    # Строка также не должна совпадать с зарезервированными словами
    t.type = reserved.get(t.value, 'STRING')
    
    if t.type == 'STRING' and t.value.startswith('"') and t.value.endswith('"') and not t.value.endswith(r'\"'):
        t.value = t.value.replace(r"\\", "\\") #Заменяем \\ на \
        t.value = t.value.replace(r'\"', r'"') #Заменяем \" на "
        t.value = t.value[1:-1] #Удаляем кавычки с начала и с конца, "abc" становится abc        
    return t

#Эти токены должны учитываться в регэкспе токена STRING...
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_COLON = r':'
t_EQUAL = r'='
t_GREATER = r'>'
t_GREATER_EQ = r'>='
t_LESS = r'<'
t_LESS_EQ = r'<='
t_LIKE = r'~'

# A string containing ignored characters (spaces and tabs)
t_ignore  = ' \t\n\r'


# Error handling rule
def t_error(t):
    raise LexError("Lexical error in '{}'".format(t.value[0]))


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
    
    #Если совпадает с зарезервированным словом
    if reserved.get(string) is not None:
        return True
    
    return False


def build_lexer():    
    '''Строит лексический анализатор на основе всех определенных здесь токенов.'''
    lexer = lex.lex(errorlog=consts.lex_errorlog)
    return lexer

