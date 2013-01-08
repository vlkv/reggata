# -*- coding: utf-8 -*-
'''
Copyright 2010 Vitaly Volkov
Created on 27.11.2010

Module consists of classes, which represent nodes of syntax tree of
reggata query language.
'''
import reggata.helpers as helpers
from reggata.data import db_schema


class QueryExpression(object):
    '''
        This is a base class for all nodes of syntax tree.
    '''
    def interpret(self):
        raise NotImplementedError("This is an abstract method.")


class CompoundQuery(QueryExpression):
    '''
        Node, representing a compound expression of a query
    (that consists of several SQL queries).
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
        This node represents a triple (FieldName, Operation, Value).
    '''
    def __init__(self, name, op, value):
        self.name = name
        self.op = op
        self.value = value

    def interpret(self, i=0):
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

        #Now value may be of type: str, int or float
        if self.op in ['=', '>', '>=', '<', '<='] and type(value) in [int, float]:
            return """ CAST(if{0}.field_value as REAL) {1} {2} """.format(i, self.op, value)
        elif self.op == '~':
            return """ if{0}.field_value LIKE '{1}' """.format(i, value)
        else:
            return """ if{0}.field_value {1} '{2}' """.format(i, self.op, value)


class SimpleQuery(QueryExpression):
    '''
        This is a base class for all simple expressions
    (those represented by a single SQL query).
    '''
    def __init__(self):
        self.extra_paths = []
        self.extra_users = []
        self.extra_titles = []

    def add_extra_clause(self, ext):
        if ext.type == 'USER':
            self.extra_users.append(ext)
        elif ext.type == 'PATH':
            self.extra_paths.append(ext)
        elif ext.type == 'TITLE':
            self.extra_titles.append(ext)
        else:
            raise Exception("Unexpected type of extra_clause {}".format(str(ext.type)))

class SingleExtraClause(SimpleQuery):

    def __init__(self):
        super(SingleExtraClause, self).__init__()

    def interpret(self):
        #extra_users_str
        if len(self.extra_users) > 0:
            comma_list = helpers.to_commalist(self.extra_users, lambda x: "'" + x.interpret() + "'", ", ")
            extra_users_str = " i.user_login IN (" + comma_list + ") "
        else:
            extra_users_str = " 1 "

        #extra_paths_str
        if len(self.extra_paths) > 0:
            extra_paths_str = helpers.to_commalist( \
                self.extra_paths, lambda x: "data_refs.url LIKE '" + x.interpret() + "%'", " OR ")
        else:
            extra_paths_str = " 1 "

        #extra_titles_str
        if len(self.extra_titles) > 0:
            extra_titles_str = helpers.to_commalist( \
                self.extra_titles, lambda x: "i.title LIKE '%" + x.interpret() + "%'", " OR ")
        else:
            extra_titles_str = " 1 "

        #TODO filter items by item_tags.user_login and item_fields.user_login also
        s = '''
        --SingleExtraClause.interpret()
        select distinct
            i.*,
            ''' + db_schema.DataRef._sql_from() + '''
        from items i
        left join data_refs on data_refs.id = i.data_ref_id
            where (''' + extra_users_str + ''')
            and (''' + extra_paths_str + ''')
            and (''' + extra_titles_str + ''')
        '''
        return s

class FieldsConjunction(SimpleQuery):
    '''
        This is a conjunction of FieldOpVal. For example:
    Field1=Value1 AND Field2=Value2 AND Field3=Value3

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
            f2.name = 'Author' and if2.field_value LIKE 'Dostoevsky'
        and f1.name = 'Rating' and CAST(if1.field_value as REAL) < 5
        and f3.name = 'Year' and if3.field_value = '2010'
    '''
    # Maybe we should add here a condition like:
    # ... and if1.field_id <> if2.field_id
    # ... and if2.field_id <> if3.field_id and if1.field_id <> if3.field_id
    # ... and so on?..

    def __init__(self):
        super(FieldsConjunction, self).__init__()
        self.field_op_vals = []


    def interpret(self):
        #extra_users_str
        if len(self.extra_users) > 0:
            users_comma_list = helpers.to_commalist(self.extra_users,
                                                    lambda x: "'" + x.interpret() + "'", ", ")
        else:
            users_comma_list = None

        #extra_titles_str
        if len(self.extra_titles) > 0:
            extra_titles_str = helpers.to_commalist( \
                self.extra_titles, lambda x: "i.title LIKE '%" + x.interpret() + "%'", " OR ")
        else:
            extra_titles_str = " 1 "

        from_parts = []
        where_parts = []
        i = 1
        for field_op_val in self.field_op_vals:

            extra_users_str = "and if{0}.user_login IN ({1})".format(i, users_comma_list) \
                if users_comma_list else ""

            from_part = '''
            inner join items_fields if{0} on if{0}.item_id = i.id
            inner join fields f{0} on f{0}.id = if{0}.field_id '''.format(str(i))
            if i > 1:
                from_part = from_part + ''' and if{0}.field_id <> if{1}.field_id '''.format(i-1, i)
            from_parts.append(from_part)

            where_part = '''f{0}.name = '{1}' and {2} {3}'''.format(i, field_op_val.name,
                                                                    field_op_val.interpret(i),
                                                                    extra_users_str)
            where_parts.append(where_part)
            i = i + 1

        #from_str
        from_str = ""
        for from_part in from_parts:
            from_str = from_str + from_part

        #where_str
        where_str = helpers.to_commalist(where_parts, lambda x: x, " and \n")



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
            and (''' + extra_titles_str + ''')
        '''
        return s

    def add_field_op_val(self, field_op_val):
        self.field_op_vals.append(field_op_val)



class Tag(QueryExpression):
    '''
        A syntax tree node, representing a Tag.
    '''
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
        Conjunction of Tags or their or their negations. For example:
    "Book AND Programming AND NOT Design"

    SQL query for this:

    select * from items i
    left join items_tags it on i.id = it.item_id
    left join tags t on t.id = it.tag_id
    where
        (t.name='Book' or t.name='Programming')    --yes_tags_str

        and i.id NOT IN (select i.id from items i        --no_tags_str
        left join items_tags it on i.id = it.item_id
        left join tags t on t.id = it.tag_id
        where t.name='Design')

        group by i.id having count(*)=2                  --group_by_having
    '''

    def __init__(self):
        super(TagsConjunction, self).__init__()

        self.yes_tags = []
        self.no_tags = []


    def interpret(self):
        #yes_tags_str, group_by_having
        group_by_having = ""
        if len(self.yes_tags) > 0:
            yes_tags_str = helpers.to_commalist(self.yes_tags,
                                                lambda x: "t.name='" + x.interpret() + "'", " or ")

            if len(self.yes_tags) > 1:
                group_by_having = " group by i.id having count(*)={} ".format(len(self.yes_tags))
        else:
            yes_tags_str = " 1 "

        #extra_users_str
        if len(self.extra_users) > 0:
            comma_list = helpers.to_commalist(self.extra_users,
                                              lambda x: "'" + x.interpret() + "'", ", ")
            extra_users_str = " it.user_login IN (" + comma_list + ") "
        else:
            extra_users_str = " 1 "

        #extra_paths_str
        if len(self.extra_paths) > 0:
            extra_paths_str = helpers.to_commalist( \
                self.extra_paths, lambda x: "data_refs.url LIKE '" + x.interpret() + "%'", " OR ")
        else:
            extra_paths_str = " 1 "

        #extra_titles_str
        if len(self.extra_titles) > 0:
            extra_titles_str = helpers.to_commalist( \
                self.extra_titles, lambda x: "i.title LIKE '%" + x.interpret() + "%'", " OR ")
        else:
            extra_titles_str = " 1 "


        #no_tags_str
        if len(self.no_tags) > 0:
            no_tags_str = " i.id NOT IN (select i.id from items i " + \
            " left join items_tags it on i.id = it.item_id " + \
            " left join tags t on t.id = it.tag_id " + \
            " where (" + helpers.to_commalist(self.no_tags,
                lambda x: "t.name='" + x.interpret() + "'", " or ") + ") " + ") "
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
            and (''' + extra_titles_str + ''')
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
        ExtraClause is a part of query, which allow you to restrict items
    by a user, file physical path. For example:

    "user:vlkv user:sunshine path:music/favorite/new"

        This will query all items of "vlkv" OR "sunshine" users, and files of those items
    should be located in subdirectory "music/favorite/new".
    '''

    def __init__(self, type=None, value=None):
        self.type = type #'USER', 'PATH' or 'TITLE'
        self.value = value # User login or repository path

    def interpret(self):
        return str(self.value)
