select t.name as name, count(*) as c
   from items i, tags t
   join items_tags it on it.tag_id = t.id and it.item_id = i.id and i.alive   
where
    1
group by t.name
ORDER BY t.name
