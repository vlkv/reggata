
--Получение связанных тегов (related tags)
select t.name, count(*)
    from tags t
    join items_tags it on it.tag_id = t.id
where
    it.item_id IN (
        select it1.item_id
            from items_tags it1
            join items_tags it2 on it2.item_id=it1.item_id AND it2.tag_id > it1.tag_id
            --join items_tags it3 on it3.item_id=it2.item_id AND it3.tag_id > it2.tag_id
        where 
            it1.tag_id = 11 
            AND it2.tag_id = 12
            --AND it3.tag_id = 18
    )
    AND t.id != 11
    AND t.id != 12
    --AND t.id != 18
    --Важно, чтобы эти id-шники следовали по возрастанию
group by t.name
ORDER BY count(*) DESC


