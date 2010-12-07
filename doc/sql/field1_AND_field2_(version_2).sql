select * 
from 
(select 
    i.id, i.title
--    ,if1.item_id as if1_i, if1.field_id as if1_f, f1.name as f1_name, if1.field_value as if1_fv

    from items i
    inner join items_fields if1 on if1.item_id = i.id
    inner join fields f1 on f1.id = if1.field_id
    where 
            f1.name = 'Автор' and if1.field_value LIKE 'Васькин'

INTERSECT

select 
    i.id, i.title
--    ,if1.item_id as if1_i, if1.field_id as if1_f, f1.name as f1_name, if1.field_value as if1_fv

    from items i
    inner join items_fields if1 on if1.item_id = i.id
    inner join fields f1 on f1.id = if1.field_id
    where 
            f1.name = 'Рейтинг' and CAST(if1.field_value as REAL) <= 5

INTERSECT

select 
    i.id, i.title
--    ,if1.item_id as if1_i, if1.field_id as if1_f, f1.name as f1_name, if1.field_value as if1_fv

    from items i
    inner join items_fields if1 on if1.item_id = i.id
    inner join fields f1 on f1.id = if1.field_id
    where 
            f1.name = 'Год' and if1.field_value = '2010'

) as sub