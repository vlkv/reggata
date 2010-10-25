
--Выборка "Тег1 И Тег2 из заданной поддиректории (и вложенных)"
select * from items i 
left join items_tags it on it.item_id = i.id
left join tags t on t.id = it.tag_id
left join items_data_refs idr on i.id = idr.item_id
left join data_refs dr on idr.data_ref_id = dr.id
where
    (t.name='Книга' or t.name='Программирование')
    and dr.url like 'books/new%'
group by i.id 
having count(*)=2

