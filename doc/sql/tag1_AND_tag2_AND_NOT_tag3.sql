
--Тег1 И Тег2 И НЕ Тег3
select * from items i 
left join items_tags it on i.id = it.item_id
left join tags t on t.id = it.tag_id
where
    (t.name='Книга' or t.name='Программирование')
    and i.id NOT IN (select i.id from items i left join items_tags it on i.id = it.item_id left join tags t on t.id = it.tag_id
    where t.name='Проектирование')
group by i.id 
having count(*)=2

