
--Получение значений id для списка тегов
select * from tags t
where t.name in ('ООП', 'Книга', 'Java')
order by t.id
