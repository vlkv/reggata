'''
Created on 27.11.2010

Содержит различные вспомогательные функции пакета parsers.
'''
import re


def escape(string, esc_rules):
    for esc_rule in esc_rules:
        esc_seq, raw_seq = esc_rule
        string = re.sub(raw_seq, esc_seq, string)
    return string


def unescape(string, esc_rules):
    for esc_rule in esc_rules:
        esc_seq, raw_seq = esc_rule
        string = re.sub(esc_seq, raw_seq, string)
    return string
    
             
        
        
if __name__ == "__main__":
    
    one = '\\'
    
    unescaped = r'we \need\ to "escape" this string!'
    print(re.sub(r'\\', "\\", unescaped))
    #print(unescaped.replace('\\', r'\\'))
    m = re.findall(r'\\', unescaped)
    print(m)
    
    #, (r'\\\\', '\\')
    
    
    (r'\\"', r'"')
    
        



