
--Выборка по полям: Поле1=знач1 И Поле2=знач2
select * 
from items i
join items_fields i_f1 on i_f1.item_id = i.id
join items_fields i_f2 on i_f2.item_id = i.id and i_f1.field_id < i_f2.field_id
where 
        i_f1.field_id = 1 and i_f1.field_value LIKE '%Эккель%' --Автор
    and i_f2.field_id = 2 and CAST(i_f2.field_value as REAL) >= 5 --Рейтинг
    --Очень важно, чтобы id-шники полей следовали по возрастанию (в том же порядке, как склеивались таблицы)
    

