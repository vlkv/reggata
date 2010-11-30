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

Токены для парсера tags_def_parser.
'''
from ply import lex
import re

#Список типов токенов
tokens = [
   'STRING', #Строка, которая либо отдельное слово, либо в двойных кавычках все что угодно
]

# Строка. Если содержит пробелы или двойные кавычки или обратный слеш, то
# должна быть в двойных кавычках. Для строки в кавычках есть две escape 
# последовательности:
# 1) \" для отображения кавычки "
# 2) \\ для отображения слеша \
# Если строка содержит :, то ее тоже нужно заключать в двойные кавычки
def t_STRING(t):
    #r'''"(\\["\\]|[^"\\])*"|[\w]+''' #Тут пробелы лишние нельзя ставить!!!
    r'"(\\["\\]|[^"\\])*"|[^\s:"\\]+' #Тут пробелы лишние нельзя ставить!!!    
    if t.type == 'STRING' and t.value.startswith('"') and t.value.endswith('"') and not t.value.endswith(r'\"'):
        t.value = t.value.replace(r"\\", "\\") #Заменяем \\ на \
        t.value = t.value.replace(r'\"', r'"') #Заменяем \" на "
        t.value = t.value[1:-1] #Удаляем кавычки с начала и с конца, "abc" становится abc        
    return t

# Строка, содержащая игнорируемые символы (пробелы, табы и проч.)
t_ignore  = ' \t\n\r'

# Что делать, если возникнет ошибка
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1) #Пропускаем текущий символ и переходим к следующему


def build_lexer():    
    '''Строит лексический анализатор на основе всех определенных здесь токенов.'''
    lexer = lex.lex()
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

