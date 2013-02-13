# -*- coding: utf-8 -*-
'''
Copyright 2010 Vitaly Volkov
Created on 28.11.2010

Tokens for parser from definition_parser module.
'''

from ply import lex
import re
import reggata.consts as consts
from reggata.errors import LexError

# Token types:
tokens = [
   'STRING', # String as a single word (without whitespaces) or a quoted string
   'COLON',  # This is a delimiter between field name and field value
]


def t_STRING(t):
    r'"(\\["\\]|[^"\\])*"|([^\s():=><~"\\])+' #Тут пробелы лишние нельзя ставить!!!
    # For explanation of the regexp look here: query_tokens.t_STRING
    if t.type == 'STRING' \
    and t.value.startswith('"') \
    and t.value.endswith('"') \
    and not t.value.endswith(r'\"'):
        t.value = t.value.replace(r"\\", "\\")
        t.value = t.value.replace(r'\"', r'"')
        t.value = t.value[1:-1]
    return t

t_COLON = r':'

# Symbols that are ignored
t_ignore  = ' \t\n\r'


def t_error(t):
    raise LexError("Lexical error in '{}'".format(t.value[0]))


def build_lexer():
    # TODO: use file for logging
    #lex_errorlog = ply.lex.PlyLogger(open(os.path.join(USER_CONFIG_DIR, "lex.log"), "w"))
    lex_errorlog = lex.NullLogger()
    lexer = lex.lex(errorlog=lex_errorlog)
    return lexer


def needs_quote(string):
    if re.search(r'\s', string):
        return True

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
