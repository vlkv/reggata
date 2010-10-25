
--Получение связанных тегов (related tags)
--Способ работает только для получения тегов, связанных только с одним тегом!!!
select dt.name, count(*) 
from tags st
inner join items_tags sit on sit.tag_id = st.id
inner join items i on sit.item_id = i.id
inner join items_tags dit on i.id = dit.item_id
inner join tags dt on dit.tag_id = dt.id

where
    (st.name='Книга')
    and st.id <> dt.id
group by dt.name
ORDER BY count(*) DESC



