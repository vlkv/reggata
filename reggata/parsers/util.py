# -*- coding: utf-8 -*-
'''
Created on 27.11.2010
'''
import re
from helpers import is_none_or_empty


def escape(string):
    # Escaping slashes first
    string = re.sub(r'\\', r'\\\\', string)
    
    # And only then, escaping all the other symbols
    string = re.sub(r'"', r'\"', string)    
    return string


def unescape(string):
    string = re.sub(r'\\"', r'"', string)
    string = re.sub(r'\\\\', r'\\', string)
    return string


def quote(string):
    '''
        Escapes all symbols of the given string and puts the string
    in a quotes. Returns modified string.
    '''
    return '"' + escape(string) + '"'
    

def unquote(string):
    '''
        Removes quotes and unescapes all symbols of the string.
    Returns modified string.
    '''
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

    # If you will call escape two times - you would have a mess as a result
    print(escape(escaped))
    
    m = re.findall(r'"', unescaped)
    print(m)
    
