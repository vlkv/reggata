# -*- coding: utf-8 -*-
'''
Copyright 2010 Vitaly Volkov
Created on 28.11.2010

Parser for text definition of tags and fields.
'''
import ply.yacc as yacc
from reggata.parsers.definition_tokens import tokens, build_lexer
from reggata.errors import YaccError
from reggata import consts

def p_definition_empty(p):
    '''definition :
    '''
    p[0] = ([], []) #Tuple (list_of_tags, list_of_fields)

def p_definition_fields(p):
    '''definition : definition field_value_pair
    '''
    fields = p[1][1]
    fields.append(p[2])
    p[0] = (p[1][0], fields)

def p_definition_tags(p):
    '''definition : definition tag
    '''
    tags = p[1][0]
    tags.append(p[2])
    p[0] = (tags, p[1][1])

def p_field_value_pair(p):
    '''field_value_pair : field COLON value
    '''
    p[0] = (p[1], p[3])

def p_field(p):
    '''field : STRING
    '''
    p[0] = p[1]

def p_value(p):
    '''value : STRING
    '''
    p[0] = p[1]

def p_tags_def_expression_empty(p):
    '''tags_def_expression :
    '''
    p[0] = []

def p_tag(p):
    '''tag : STRING
    '''
    p[0] = p[1]


def p_error(p):
    raise YaccError("Syntax error in '{}'".format(str(p)))


lexer = build_lexer()

tokens  # This line is needed to supress warning that 'tokens is unused'
parsetabPyDir = consts.USER_CONFIG_DIR
parser = yacc.yacc(errorlog=consts.yacc_errorlog,
                   debug=(1 if consts.DEBUG else 0), # If debug yacc creates parser.out log file
                   tabmodule="parsetab_def",
                   outputdir=parsetabPyDir)


def parse(text):
    return parser.parse(text, lexer=lexer)


if __name__ == '__main__':
    data = r'''
    Tag1 : "Slash\\:quote\" end"
    and:"tag 2" LOOK
    user : "asdf"
    TAG AND MORE TAGS
    '''
    res = parse(data)
    print(res)
