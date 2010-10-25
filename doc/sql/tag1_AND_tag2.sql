
--Выборка "Тег1 И Тег2"
select * from items i 
left join items_tags it on it.item_id = i.id
left join tags t on t.id = it.tag_id
where
    t.name='Книга' or t.name='Программирование'
group by i.id 
having count(*)=2
