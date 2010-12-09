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

Created on 27.11.2010

Модуль содержит классы, представляющие собой узлы дерева разбора предложений 
языка запросов.
'''
import consts
import helpers
from user_config import UserConfig
import db_schema
from helpers import tr, to_commalist


class QueryExpression(object):
    '''Базовый класс для всех классов-узлов синтаксического дерева разбора.'''
    
    def interpret(self):
        raise NotImplementedError(tr('This is an abstract method.'))


class CompoundQuery(QueryExpression):
    '''
    Узел, представляющий составное выражение запроса. 
    '''
    
    def __init__(self, elem=None):
        if elem:
            self.elems = [elem]
        else:
            self.elems = []
        
    def and_elem(self, elem):
        self.elems.append("\n INTERSECT \n")
        self.elems.append(elem)
    
    def or_elem(self, elem):
        self.elems.append("\n UNION \n")
        self.elems.append(elem)
    
    def and_not_elem(self, elem):
        self.elems.append("\n EXCEPT \n")
        self.elems.append(elem)
    
    def add_extra_clause(self, ext):
        for elem in self.elems:
            if isinstance(elem, SimpleQuery):
                elem.add_extra_clause(ext)

    
        
    def interpret(self):
        s = ""
        for elem in self.elems:
                            
            if isinstance(elem, QueryExpression):
                s = s + elem.interpret()
            else:                
                s = s + elem
        return s
                 

class FieldOpVal(QueryExpression):
    '''
    Узел синт. дерева для представления тройки (ИмяПоля,Операция,Значение).
    '''
    
    def __init__(self, name, op, value):
        self.name = name
        self.op = op
        self.value = value
        
    def interpret(self, i=0):
        #Пробуем преобразовать value в число
        value = self.value
        ok = False
        try:
            value = int(self.value)
            ok = True
        except:
            pass
    
        if not ok:
            try:
                value = float(self.value)
            except:
                pass
        
        #Теперь value может иметь тип str, int или float
        if self.op in ['=', '>', '>=', '<', '<='] and type(value) in [int, float]:
            return """ CAST(if{0}.field_value as REAL) {1} {2} """.format(i, self.op, value)
        elif self.op == '~':
            return """ if{0}.field_value LIKE '{1}' """.format(i, value)
        else:
            return """ if{0}.field_value {1} '{2}' """.format(i, self.op, value)


class SimpleQuery(QueryExpression):
    '''
    Базовый класс для всех простых выражений (которые представляют собой один SQL запрос).
    '''
    def __init__(self):
        #Список дополнительных условий USER и PATH
        self.extra_paths = []
        self.extra_users = []
    
    def add_extra_clause(self, ext):
        if ext.type == 'USER':
            self.extra_users.append(ext)
        elif ext.type == 'PATH':
            self.extra_paths.append(ext)
        else:
            raise Exception(tr("Unexpected type of extra_clause {}").format(str(ext.type)))
        
    
class FieldsConjunction(SimpleQuery):
    '''
    Конъюнкция объектов FieldOpVal.
    
    --Выборка по полям: Поле1=знач1 И Поле2=знач2 И Поле3=значе3
    select 
        i.id, i.title,
        if1.item_id as if1_i, if1.field_id as if1_f, f1.name as f1_name, if1.field_value as if1_fv,  
        if2.item_id as if2_i, if2.field_id as if2_f, f2.name as f2_name, if2.field_value as if2_fv,
        if3.item_id as if3_i, if3.field_id as if3_f, f3.name as f3_name, if3.field_value as if3_fv
    from items i
        inner join items_fields if1 on if1.item_id = i.id
        inner join fields f1 on f1.id = if1.field_id
        inner join items_fields if2 on if2.item_id = i.id and if1.field_id <> if2.field_id
        inner join fields f2 on f2.id = if2.field_id    
        inner join items_fields if3 on if3.item_id = i.id and if2.field_id <> if3.field_id
        inner join fields f3 on f3.id = if3.field_id    
    where 
            f2.name = 'Автор' and if2.field_value LIKE 'Васькин'
        and f1.name = 'Рейтинг' and CAST(if1.field_value as REAL) < 5
        and f3.name = 'Год' and if3.field_value = '2010'
        --Вот такому запросу неважно, в каком порядке следуют запрашиваемые поля.
        --Однако, мне кажется он будет выполняться медленно!
    '''
    
    #TODO Может быть тут поставить в join-ах еще доп. условие вида
    # ... and if1.field_id <> if2.field_id
    # ... and if2.field_id <> if3.field_id and if1.field_id <> if3.field_id
    # ... и т.д.? 
    
    def __init__(self):
        super(FieldsConjunction, self).__init__()
        
        self.field_op_vals = []
        
        
    
    
    
    def interpret(self):
        
        #extra_users_str
        if len(self.extra_users) > 0:
            users_comma_list = helpers.to_commalist(self.extra_users, lambda x: "'" + x.interpret() + "'", ", ") 
        else:
            users_comma_list = None
            
        from_parts = []
        where_parts = []
        i = 1
        for field_op_val in self.field_op_vals:
            
            extra_users_str = "and if{0}.user_login IN ({1})".format(i, users_comma_list) if users_comma_list else ""
            
            from_part = '''
            inner join items_fields if{0} on if{0}.item_id = i.id
            inner join fields f{0} on f{0}.id = if{0}.field_id '''.format(str(i))
            if i > 1:
                from_part = from_part + ''' and if{0}.field_id <> if{1}.field_id '''.format(i-1, i)
            from_parts.append(from_part)
            
            where_part = '''f{0}.name = '{1}' and {2} {3}'''.format(i, field_op_val.name, field_op_val.interpret(i), extra_users_str)
            where_parts.append(where_part)
            i = i + 1
        
        #from_str
        from_str = ""
        for from_part in from_parts:
            from_str = from_str + from_part
            
        #where_str
        where_str = to_commalist(where_parts, lambda x: x, " and \n")
        
        
        
        #extra_paths_str
        if len(self.extra_paths) > 0:
            extra_paths_str = helpers.to_commalist( \
                self.extra_paths, lambda x: "data_refs.url LIKE '" + x.interpret() + "%'", " OR ")
        else:
            extra_paths_str = " 1 "
        
        s = '''
        --FieldsConjunction.interpret()
        select distinct 
            i.*, 
            ''' + db_schema.DataRef._sql_from() + '''
        from items i
        ''' + from_str + '''             
        left join data_refs on data_refs.id = i.data_ref_id
            where (''' + where_str + ''')
            and (''' + extra_paths_str + ''') 
        '''            
        return s
        
    def add_field_op_val(self, field_op_val):
        self.field_op_vals.append(field_op_val)



class Tag(QueryExpression):
    '''Узел синтаксического дерева для представления тегов.'''    
    
    def __init__(self, name, is_negative=False):
        self.name = name
        self.is_negative = is_negative
    
    def negate(self):
        self.is_negative = not self.is_negative
        
    def interpret(self):
        return self.name
    
    def __str__(self):
        return self.name



class TagsConjunction(SimpleQuery):
    '''
    Конъюнкция тегов или их отрицаний, например:
    "Книга И Программирование И НЕ Проектирование"
    
    Реализация такого запроса на SQL:
    
    select * from items i 
    left join items_tags it on i.id = it.item_id
    left join tags t on t.id = it.tag_id
    where
        (t.name='Книга' or t.name='Программирование')    --yes_tags_str
        
        and i.id NOT IN (select i.id from items i        --no_tags_str
        left join items_tags it on i.id = it.item_id 
        left join tags t on t.id = it.tag_id
        where t.name='Проектирование')
        
        group by i.id having count(*)=2                  --group_by_having
    '''    
    
    def __init__(self):
        super(TagsConjunction, self).__init__()
        
        #Списки для хранения тегов
        self.yes_tags = []
        self.no_tags = []
        
        
    
    def interpret(self):
        #yes_tags_str, group_by_having
        group_by_having = ""
        if len(self.yes_tags) > 0:
            yes_tags_str = helpers.to_commalist(self.yes_tags, lambda x: "t.name='" + x.interpret() + "'", " or ")
            
            if len(self.yes_tags) > 1:
                group_by_having = " group by i.id having count(*)={} ".format(len(self.yes_tags))
        else:
            yes_tags_str = " 1 "
            
        #extra_users_str
        if len(self.extra_users) > 0:
            comma_list = helpers.to_commalist(self.extra_users, lambda x: "'" + x.interpret() + "'", ", ") 
            extra_users_str = " it.user_login IN (" + comma_list + ") "
        else:
            extra_users_str = " 1 "
        
        #extra_paths_str
        if len(self.extra_paths) > 0:
            extra_paths_str = helpers.to_commalist( \
                self.extra_paths, lambda x: "data_refs.url LIKE '" + x.interpret() + "%'", " OR ")
        else:
            extra_paths_str = " 1 "
            
        
        #no_tags_str
        if len(self.no_tags) > 0:
            no_tags_str = " i.id NOT IN (select i.id from items i " + \
            " left join items_tags it on i.id = it.item_id " + \
            " left join tags t on t.id = it.tag_id " + \
            " where (" + helpers.to_commalist(self.no_tags, lambda x: "t.name='" + x.interpret() + "'", " or ") + ") " + ") "
        else:
            no_tags_str = " 1 "
        
        s = '''
        --TagsConjunction.interpret()
        select distinct 
            i.*, 
            ''' + db_schema.DataRef._sql_from() + '''
        from items i 
        left join items_tags it on i.id = it.item_id 
        left join tags t on t.id = it.tag_id
        left join data_refs on data_refs.id = i.data_ref_id
            where (''' + yes_tags_str + ''') 
            and (''' + extra_users_str + ''') 
            and (''' + no_tags_str + ''')
            and (''' + extra_paths_str + ''')
            ''' + group_by_having            
        return s
    
    @property
    def tags(self):
        return self.yes_tags + self.no_tags
    
    def add_tag(self, tag):
        if tag.is_negative:
            self.no_tags.append(tag)
        else:
            self.yes_tags.append(tag)
        
        
class ExtraClause(QueryExpression):
    '''
    Дополнительные условия в запросе, определяющие ограничения на пользователей и на 
    физическое расположение файлов, привязанных к элементу.
    
    Например: "user:vlkv user:sunshine path:music/favorite/new"
    Это будет означать запрос элементов, принадлежащих vlkv ИЛИ sunshine И 
    физически размещенных в поддиректории хранилища music/favorite/new. 
    '''

    def __init__(self, type=None, value=None):
        self.type = type #'USER' или 'PATH'
        self.value = value #логин пользователя или путь в хранилище
            
    def interpret(self):
        return str(self.value)



