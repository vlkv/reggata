'''
Created on 27.11.2010

Содержит различные вспомогательные функции пакета parsers.
'''
import re


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
        
        
if __name__ == "__main__":
        
    unescaped = r'This string should be \properly\ "escaped"!'
    print(unescaped)
    print(escape(unescaped))
    
    escaped = r'Is this \\string\\ un-\"escaped\"?'
    print(escaped)
    print(unescape(escaped))

    
    m = re.findall(r'"', unescaped)
    print(m)
    
