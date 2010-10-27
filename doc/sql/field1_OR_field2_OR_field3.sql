

--Выборка Поле1=знач1 ИЛИ Поле2=знач2 ИЛИ Поле3=знач3
select * from items i
join items_fields i_f on i_f.item_id = i.id
join fields f on f.id = i_f.field_id
where
    f.name = 'Рейтинг' and i_f.field_value = 5
    or f.name = 'Рейтинг' and i_f.field_value = 10
    or f.name = 'Издание' and i_f.field_value = '4-е'

