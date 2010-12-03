# -*- coding: utf-8 -*-
'''
Created on 27.11.2010

Содержит различные вспомогательные функции пакета parsers.
'''
import re
from helpers import is_none_or_empty


def escape(string):
    #Сначала escap-им слеши
    string = re.sub(r'\\', r'\\\\', string)
    #Только потом все остальные символы!
    string = re.sub(r'"', r'\"', string)    
    return string


def unescape(string):
    string = re.sub(r'\\"', r'"', string)
    string = re.sub(r'\\\\', r'\\', string)
    return string

def quote(string):
    '''Заключает string в кавычки и escape-ит символы внутри этой строки.'''
    return '"' + escape(string) + '"'
    

def unquote(string):
    '''Убрать кавычки (если есть) и раскрыть все escape последовательности. '''
    if not is_none_or_empty(string) and string.startswith('"') \
    and string.endswith('"') and not string.endswith(r'\"'):
        string = string[1:-1]
        return unescape(string)


        
if __name__ == "__main__":
        
    unescaped = r'This string should be \properly\ "escaped"!'
    print(unescaped)
    print(escape(unescaped))
    
    escaped = r'Is this \\string\\ un-\"escaped\"?'
    print(escaped)
    print(unescape(escaped))

    #А если сделать так, то будет уже каша - два раза применятся escape-последовательности
    print(escape(escaped))
    
    m = re.findall(r'"', unescaped)
    print(m)
    
