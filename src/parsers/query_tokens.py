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

'''
import ply.lex as lex
import re
from helpers import tr


AND_OPERATOR = tr('and')
OR_OPERATOR = tr('or')
NOT_OPERATOR = tr('not')
USER_KEYWORD = tr('user')
PATH_KEYWORD = tr('path')

#Зарезервированные слова и соответствующие им типы токенов
#Я хочу, чтобы операции and, or, not и др. были в нескольких вариантах.
#Например, чтобы and можно было записать как and, And, AND
reserved = dict()
for tuple in [(AND_OPERATOR, 'AND'), (OR_OPERATOR, 'OR'), (NOT_OPERATOR, 'NOT'), 
              (USER_KEYWORD, 'USER'), (PATH_KEYWORD, 'PATH')]:
    keyword, type = tuple
    reserved[keyword.capitalize()] = type
    reserved[keyword.upper()] = type
    reserved[keyword.lower()] = type
#Правда ply выводит warning сообщения о том, что токен AND (OR и др.) определен более одного раза...
#Но работает, как мне хочется.


#Список типов токенов
tokens = [
   'STRING', #Строка, которая либо отдельное слово, либо в двойных кавычках все что угодно
   'LPAREN', #Открывающая круглая скобка ) 
   'RPAREN', #Закрывающая круглая скобка )
   'COLON', #Двоеточие : (ставится после ключевых слов user и после path)
] + list(reserved.values())

# Строка. Если содержит пробелы или двойные кавычки или обратный слеш, то
# должна быть в двойных кавычках. Для строки в кавычках есть две escape 
# последовательности:
# 1) \" для отображения кавычки "
# 2) \\ для отображения слеша \
def t_STRING(t):
    r'''"(\\["\\]|[^"\\])*"|[\w]+''' #Тут пробелы лишние нельзя ставить!!!
    t.type = reserved.get(t.value, 'STRING')
    if t.type == 'STRING' and t.value.startswith('"') and t.value.endswith('"') and not t.value.endswith(r'\"'):
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


def need_quote(string):
    '''Возвращает True, если строку string нужно заключить в кавычки, чтобы она
    правильно была распознана как токен типа 'STRING'. 
    Это вспомогательная функция, не влияющая на работу парсера.'''
    
    #Если внутри строки есть пробелы
    if re.search(r'\s', string):
        return True
    
    #Если не подходит под регэксп токена STRING
    m = re.match(t_STRING.__doc__, string)
    if m is None or m.group() != string:
        return True
    
    #Если совпадает с зарезервированным словом
    if reserved.get(string) is not None:
        return True
    
    return False

def quote(string):
    '''Заключает string в кавычки и escape-ит нужные символы внутри этой строки.'''
    
    #string = string.replace_all(r'"', r'\"')
    #TODO
    pass

def unquote(string):
    '''Убрать кавычки и раскрыть все escape последовательности как есть. '''
    pass


def build_lexer():    
    '''Строит лексический анализатор на основе всех определенных здесь токенов.'''
    lexer = lex.lex()
    return lexer

