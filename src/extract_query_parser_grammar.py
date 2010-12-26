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

Created on 24.10.2010

Модуль извлекает грамматику из query_parser.py и сохраняет ее в отдельный файл.
'''

import parsers.query_parser as qp
import os


if __name__ == '__main__':

    s = ""
    for i in dir(qp):
        if i.startswith("p_") and not i=="p_error":
            print(i)
            s += "       " + qp.__dict__.get(i).__doc__ + os.linesep
    print(s)
    
    f = open("query_parser_grammar.txt", "w")
    f.writelines(s)
    f.close()