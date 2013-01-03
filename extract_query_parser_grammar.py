# -*- coding: utf-8 -*-
'''
Created on 24.10.2010

Module extracts grammar from query_parser.py and saves it in a separate file.
'''

import parsers.query_parser as qp
import os


if __name__ == '__main__':
    s = ""
    for i in dir(qp):
        if i.startswith("p_") and not i=="p_error":
            s += "       " + qp.__dict__.get(i).__doc__ + os.linesep
    print(s)
    
    f = open("query_parser_grammar.txt", "w")
    f.writelines(s)
    f.close()
    