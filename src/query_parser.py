'''
Created on 24.10.2010

@author: vlkv
'''

import ply.lex as lex
import helpers

# List of token names.   This is always required
tokens = (
   'TAG',
   'AND',
   'NOT',
)

# Regular expression rules for simple tokens
t_TAG    = r'[a-zA-Z_0-9]+'
t_AND   = r'И'
t_NOT   = r'НЕ'

# A string containing ignored characters (spaces and tabs)
t_ignore  = ' \t\n'

# Error handling rule
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()
       
       
       
       
# Test it out
data = '''
Tag1 И Tag2 И НЕ Tag3
'''

# Give the lexer some input
lexer.input(data)

# Tokenize
while True:
    tok = lexer.token()
    if not tok: break      # No more input
    print(tok)

class tag(object):
    
    def __init__(self, name):
        self.name = name
        self.is_negative = False
    
    def negate(self):
        self.is_negative = not self.is_negative
        
    @property
    def is_negative(self):
        return self._is_negative
    
    @is_negative.setter
    def is_negative(self, value):
        self._is_negative = value 
        
        
    def interpret(self):
        return self.name
    
    def __str__(self):
        return self.name

class and_not_tag(object):
    '''
    --Тег1 И Тег2 И НЕ Тег3
    select * from items i 
    left join items_tags it on i.id = it.item_id
    left join tags t on t.id = it.tag_id
    where
        (t.name='Книга' or t.name='Программирование')
        and i.id NOT IN (select i.id from items i left join items_tags it on i.id = it.item_id left join tags t on t.id = it.tag_id
        where t.name='Проектирование')
    group by i.id 
    having count(*)=2
    '''
    _tags = []
    
    @property
    def tags(self):
        return self._tags    
    
    def add_tag(self, tag):
        self.tags.append(tag)
            
    def interpret(self):
        yes_tags = []
        not_tags = []
        for t in self.tags:
            if t.is_negative:
                not_tags.append(t)
            else:
                yes_tags.append(t)
                            
        yes_tags_str = helpers.to_commalist(yes_tags, lambda x: "t.name='" + x.interpret() + "'", ' or ')
        not_tags_str = helpers.to_commalist(not_tags, lambda x: "t.name='" + x.interpret() + "'", ' or ')
        s = ''' select * from items i 
    left join items_tags it on i.id = it.item_id
    left join tags t on t.id = it.tag_id
    where
        (''' + yes_tags_str + ''')
        and i.id NOT IN (select i.id from items i left join items_tags it on i.id = it.item_id left join tags t on t.id = it.tag_id
        where ''' + not_tags_str + ''')
    group by i.id 
    having count(*)={}'''.format(len(yes_tags))
        return s
        


import ply.yacc as yacc

def p_expression_and_not_tag(p):
    'expression : expression AND tag'
    print('p_expression_and_not_tag({}, {}, {}, {})'.format(str(p[0]), str(p[1]), str(p[2]), str(p[3])))
    if p[1] is None:
        p[1] = and_not_tag()
    p[1].add_tag(p[3])
    p[0] = p[1]
    
def p_expression_tag(p):    
    'expression : tag'
    print('p_expression_tag({}, {})'.format(str(p[0]), str(p[1])))
    exp = and_not_tag()
    exp.add_tag(p[1])
    p[0] =  exp
    
def p_tag_not(p):
    'tag : NOT TAG'
    print('p_tag_not({}, {}, {})'.format(str(p[0]), str(p[1]), str(p[2])))
    t = tag(p[2])
    t.negate()
    p[0] = t
    
def p_tag_yes(p):
    'tag : TAG'
    print('p_tag_yes({}, {})'.format(str(p[0]), str(p[1])))
    p[0] = tag(p[1])

# Error rule for syntax errors
def p_error(p):
    print("Syntax error in input! " + str(p))

# Build the parser
parser = yacc.yacc()


try:
    s = '''
     Tag1 И Tag2 И НЕ Tag3 И Tag3 И НЕ Tag56
     '''       
except EOFError as ex:
    print(str(ex))

result = parser.parse(s)
print(result.interpret())









