
--Выборка по полям: Поле1=знач1 И Поле2=знач2
select 
    i.id, i.title,
    if1.item_id as if1_i, if1.field_id as if1_f, f1.name as f1_name, if1.field_value as if1_fv,  
    if2.item_id as if2_i, if2.field_id as if2_f, f2.name as f2_name, if2.field_value as if2_fv
    from items i
    inner join items_fields if1 on if1.item_id = i.id
    inner join fields f1 on f1.id = if1.field_id
    inner join items_fields if2 on if2.item_id = i.id and if1.field_id < if2.field_id
    inner join fields f2 on f2.id = if2.field_id    
    where 
            f1.name = 'Автор' and if1.field_value LIKE 'Пупкин'
        and f2.name = 'Рейтинг' and CAST(if2.field_value as REAL) >= 5
	--Очень важно, чтобы id-шники полей следовали по возрастанию
    

	--Вот так работать не будет, т.к. id поля Рейтинг больше, чем id поля Автор
--            f2.name = 'Автор' and if2.field_value LIKE 'Пупкин'
--        and f1.name = 'Рейтинг' and CAST(if1.field_value as REAL) < 5



