CREATE TABLE "user" (
    "name" TEXT PRIMARY KEY NOT NULL,
    "password" TEXT NOT NULL, -- может быть пустой пароль, но не NULL
    "notes" TEXT,
    "group" TEXT NOT NULL -- Группа определяет права пользователя. Значения: user, admin
);

-- Объект (или элемент) хранилища данных.
CREATE TABLE "object" (
	"id" INTEGER PRIMARY KEY NOT NULL, 
	"name" TEXT NOT NULL, 
	"notes" TEXT, 
	"user_name" TEXT,
	FOREIGN KEY ("user_name") REFERENCES "user"("name")
);

CREATE TABLE "data" (
    "uri" TEXT PRIMARY KEY NOT NULL, -- Это путь к файлу относит. корня хранилища, или URL ресурса Интернет --
    "hash" TEXT, -- хеш от содержимого файла, NULL для url-ссылок --
    "date_hashed" INTEGER, -- дата/время вычисления хеша --
    "size" INTEGER NOT NULL DEFAULT 0, -- размер файла в байтах, для url ссылок равно нулю --
    "order_key" INTEGER, -- ключ для сортировки в пределах одного object-а --
	"object_id" INTEGER, -- id объекта-владельца. Может быть равен и NULL --
	"user_name" TEXT, -- пользователь, который добавил файл/url в хранилище. Может быть NULL, тогда это "ничей" файл/url --
	FOREIGN KEY ("object_id") REFERENCES "object"("id"),
	FOREIGN KEY ("user_name") REFERENCES "user"("name")
);
	
-- Тег (или ключевое слово) --
CREATE TABLE "tag" (
    "name" TEXT NOT NULL,		-- имя тега --
    "user_name" TEXT NOT NULL,	-- пользователь-владелец тега --
    "synonym_id" INTEGER,		-- id группы синонимов. Все теги имеющие одинаковые не-NULL значения этого поля считаются синонимами --
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

-- Связь между object и field много-ко-многим --
CREATE TABLE "object_field" (
    "object_id" TEXT NOT NULL,
    "field_name" TEXT NOT NULL,
    "field_user_name" TEXT NOT NULL,
    "field_value" TEXT NOT NULL,
	PRIMARY KEY ("object_id", "field_name", "field_user_name"),
	FOREIGN KEY ("object_id")  REFERENCES "object"("id"),
	FOREIGN KEY ("field_name", "field_user_name") REFERENCES "field"("name", "user_name")
);

-- Связь между object и tag много-ко-многим --
CREATE TABLE "object_tag" (
    "object_id" INTEGER NOT NULL,
    "tag_name" TEXT NOT NULL,
    "tag_user_name" TEXT NOT NULL,
	PRIMARY KEY ("object_id", "tag_name", "tag_user_name"),
	FOREIGN KEY ("object_id")  REFERENCES "object"("id"),
	FOREIGN KEY ("tag_name", "tag_user_name") REFERENCES "tag"("name", "user_name")
);

-- Группа тегов/полей. Пользователь может редактировать только свои группы но добавлять в них можно как свои так и чужие теги и поля
CREATE TABLE "bundle" (
    "name" TEXT NOT NULL,
    "user_name" TEXT NOT NULL,
    "notes" TEXT,
	PRIMARY KEY ("name", "user_name"),
	FOREIGN KEY ("user_name") REFERENCES "user"("name")
);

-- Связь между bundle и tag много-ко-многим --
CREATE TABLE "bundle_tag" (
    "bundle_name" TEXT NOT NULL,
    "bundle_user_name" TEXT NOT NULL,
    "tag_name" TEXT NOT NULL,
    "tag_user_name" TEXT NOT NULL,
	PRIMARY KEY ("bundle_name", "bundle_user_name",  "tag_name", "tag_user_name") ,
	FOREIGN KEY ("bundle_name", "bundle_user_name") REFERENCES "bundle"("name", "user_name"),
	FOREIGN KEY ("tag_name", "tag_user_name") REFERENCES "tag"("name", "user_name")
);

-- Связь между bundle и field много-ко-многим --
CREATE TABLE "bundle_field" (
    "bundle_name" TEXT NOT NULL,
    "bundle_user_name" TEXT NOT NULL,
    "field_name" TEXT NOT NULL,
    "field_user_name" TEXT NOT NULL,
	PRIMARY KEY ("bundle_name", "bundle_user_name", "field_name", "field_user_name"),
	FOREIGN KEY ("bundle_name", "bundle_user_name") REFERENCES "bundle"("name", "user_name"),
	FOREIGN KEY ("field_name", "field_user_name") REFERENCES "field"("name", "user_name")
);

