# -*- coding: utf-8 -*-
'''
Copyright 2010 Vitaly Volkov
Created on 27.11.2010

Module contains a lexical analyzer of reggata query language.
'''
import ply.lex as lex
import re
from PyQt4.QtCore import QCoreApplication
from reggata.errors import LexError
import reggata.consts as consts


AND_OPERATOR = QCoreApplication.translate("parsers", 'and', None, QCoreApplication.UnicodeUTF8)
OR_OPERATOR = QCoreApplication.translate("parsers", 'or', None, QCoreApplication.UnicodeUTF8)
NOT_OPERATOR = QCoreApplication.translate("parsers", 'not', None, QCoreApplication.UnicodeUTF8)
USER_KEYWORD = QCoreApplication.translate("parsers", 'user', None, QCoreApplication.UnicodeUTF8)
PATH_KEYWORD = QCoreApplication.translate("parsers", 'path', None, QCoreApplication.UnicodeUTF8)
TITLE_KEYWORD = QCoreApplication.translate("parsers", 'title', None, QCoreApplication.UnicodeUTF8)

# In reserved dict key is a reserved keyword, value is a token type.
reserved = dict()
for keyword, tokenType in [(AND_OPERATOR, 'AND'), (OR_OPERATOR, 'OR'), (NOT_OPERATOR, 'NOT'),
              (USER_KEYWORD, 'USER'), (PATH_KEYWORD, 'PATH'), (TITLE_KEYWORD, 'TITLE')]:
    reserved[keyword.capitalize()] = tokenType
    reserved[keyword.upper()] = tokenType
    reserved[keyword.lower()] = tokenType
# NOTE: ply displays a warning that token AND (OR and others) are defined more than once...
# But I want to be able to write: AND And and. These would be equivalent tokens.


# Token types:
tokens = [
   'STRING', # String without whitespaces and quotes or any string with double quotes around.
   'LPAREN', # Open round brace )
   'RPAREN', # Closing round brace )
   'COLON', # Colon : (is used after 'user' and 'path' keywords)

   # Operations placed between field name and it's value:
   'EQUAL',
   'GREATER',
   'GREATER_EQ',
   'LESS',
   'LESS_EQ',
   'LIKE',
] + list(reserved.values())



# This string is used to represent names of Tags, Fields and Field Values.
# And in a few other cases too.
def t_STRING(t):
    r'"(\\["\\]|[^"\\])*"|([^\s():=><~"\\])+'
    # Explanation of this regexp:
    # The first part: "(\\["\\]|[^"\\])*" String is a sequence of symbols in a double quotes,
    # that consists of escaped " and \ symbols (i.e. \" and \\) and doesn't consists of " and \ symbols.
    # The second part: ([^\s():=><~"\\])+ String is a non-zero-length unquoted sequence of symbols
    # adn doesn't consisted of whitespaces, braces, colons, and symbols > < = ~ and \

    # String should not match with any of keywords
    t.type = reserved.get(t.value, 'STRING')

    if t.type == 'STRING' \
    and t.value.startswith('"') \
    and t.value.endswith('"') \
    and not t.value.endswith(r'\"'):
        t.value = t.value.replace(r"\\", "\\") # Replace \\ with \
        t.value = t.value.replace(r'\"', r'"') # Replace \" with "
        t.value = t.value[1:-1] # Remove quotes from begining and the end. "abc" becomes just abc
    return t

# This tokens should be taken into account in regexp of STRING token...
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
    '''
        Returns True, if given string needs to be quoted to be a valid STRING token.
    '''
    if re.search(r'\s', string): #re.search() returns None if nothing found
        return True

    m = re.match(t_STRING.__doc__, string)
    if m is None or m.group() != string:
        return True

    if reserved.get(string) is not None:
        return True

    return False


def build_lexer():
    lexer = lex.lex(errorlog=consts.lex_errorlog)
    return lexer
