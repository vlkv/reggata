-- Пользователь программы
CREATE TABLE "user" (
    "name" TEXT PRIMARY KEY NOT NULL, -- имя (логин) пользователя
    "password" TEXT NOT NULL, -- может быть пустой пароль, но не NULL
    "notes" TEXT, -- Комментарии, заметки о пользователе, его описание
    "group" TEXT NOT NULL DEFAULT 'USER' -- Группа определяет права пользователя. Значения: USER, ADMIN
);

-- Элемент (объект, запись) хранилища данных
CREATE TABLE "item" (
	"id" INTEGER PRIMARY KEY NOT NULL, 
	"name" TEXT NOT NULL, 
	"notes" TEXT, 
	"user_name" TEXT, -- Пользователь-владелец (кто создал элемент)
	FOREIGN KEY ("user_name") REFERENCES "user"("name")
);

-- Ссылка на описываемую элементом информацию (данные)
CREATE TABLE "data" (
    "url" TEXT PRIMARY KEY NOT NULL, -- Это путь к файлу относит. корня хранилища, или URL ресурса Интернет
    "hash" TEXT, -- хеш от содержимого файла, NULL для url-ссылок
    "date_hashed" INTEGER, -- дата/время вычисления хеша
    "size" INTEGER NOT NULL DEFAULT 0, -- размер файла в байтах, для url ссылок равно нулю
    "order_key" INTEGER, -- ключ для сортировки в пределах одного object-а
	"item_id" INTEGER, -- id объекта-владельца. Может быть равен и NULL
	"user_name" TEXT, -- пользователь, который добавил файл/url в хранилище. Может быть NULL, тогда это "ничей" файл/url
	FOREIGN KEY ("item_id") REFERENCES "item"("id"),
	FOREIGN KEY ("user_name") REFERENCES "user"("name")
);

-- Тег (ключевое слово)
CREATE TABLE "tag" (
    "name" TEXT NOT NULL,		-- имя тега
    "user_name" TEXT NOT NULL,	-- пользователь-владелец тега
    "synonym_id" INTEGER,		-- id группы синонимов. Все теги имеющие одинаковые не-NULL значения этого поля считаются синонимами
    PRIMARY KEY ("name", "user_name"),
	FOREIGN KEY ("user_name") REFERENCES "user"("name")
);

-- Поле вида ключ=значение --
CREATE TABLE "field" (
    "name" TEXT NOT NULL,
    "user_name" TEXT NOT NULL,
    "value_type" TEXT NOT NULL DEFAULT 'STRING', -- тип данных поля. Значения: STRING, NUMBER --
    "synonym_id" INTEGER,
	PRIMARY KEY ("name", "user_name"),
	FOREIGN KEY ("user_name") REFERENCES "user"("name")
);

-- Связь между item и field много-ко-многим --
CREATE TABLE "item_field" (
    "item_id" TEXT NOT NULL,
    "field_name" TEXT NOT NULL,
    "field_user_name" TEXT NOT NULL,
    "field_value" TEXT NOT NULL,
	PRIMARY KEY ("item_id", "field_name", "field_user_name"),
	FOREIGN KEY ("item_id")  REFERENCES "item"("id"),
	FOREIGN KEY ("field_name", "field_user_name") REFERENCES "field"("name", "user_name")
);

-- Связь между item и tag много-ко-многим --
CREATE TABLE "item_tag" (
    "item_id" INTEGER NOT NULL,
    "tag_name" TEXT NOT NULL,
    "tag_user_name" TEXT NOT NULL,
	PRIMARY KEY ("item_id", "tag_name", "tag_user_name"),
	FOREIGN KEY ("item_id")  REFERENCES "item"("id"),
	FOREIGN KEY ("tag_name", "tag_user_name") REFERENCES "tag"("name", "user_name")
);

-- Группа тегов/полей. Пользователь может редактировать только свои группы 
-- но добавлять в них можно как свои так и чужие теги и поля
CREATE TABLE "bundle" (
    "name" TEXT NOT NULL,
    "user_name" TEXT NOT NULL,
    "notes" TEXT,
	PRIMARY KEY ("name", "user_name"),
	FOREIGN KEY ("user_name") REFERENCES "user"("name")
);

-- Связь между bundle и tag много-ко-многим
CREATE TABLE "bundle_tag" (
    "bundle_name" TEXT NOT NULL,
    "bundle_user_name" TEXT NOT NULL,
    "tag_name" TEXT NOT NULL,
    "tag_user_name" TEXT NOT NULL,
	PRIMARY KEY ("bundle_name", "bundle_user_name",  "tag_name", "tag_user_name") ,
	FOREIGN KEY ("bundle_name", "bundle_user_name") REFERENCES "bundle"("name", "user_name"),
	FOREIGN KEY ("tag_name", "tag_user_name") REFERENCES "tag"("name", "user_name")
);

-- Связь между bundle и field много-ко-многим
CREATE TABLE "bundle_field" (
    "bundle_name" TEXT NOT NULL,
    "bundle_user_name" TEXT NOT NULL,
    "field_name" TEXT NOT NULL,
    "field_user_name" TEXT NOT NULL,
	PRIMARY KEY ("bundle_name", "bundle_user_name", "field_name", "field_user_name"),
	FOREIGN KEY ("bundle_name", "bundle_user_name") REFERENCES "bundle"("name", "user_name"),
	FOREIGN KEY ("field_name", "field_user_name") REFERENCES "field"("name", "user_name")
);

