select distinct * 
from items i 
left join items_tags it on i.id=it.item_id 
left join tags t on t.id=it.tag_id
left join items_fields if on i.id=if.item_id
left join fields f on f.id=if.field_id
left join items_data_refs idr on idr.item_id = i.id
left join data_refs dr on idr.item_id=dr.id
where
(it.user_login='vlkv' OR if.user_login='vlkv')
--and f.name='Рейтинг' AND if.field_value=5
--	dr.url LIKE 'zim' AND
and (t.name='Программирование' OR t.name='Книга')

