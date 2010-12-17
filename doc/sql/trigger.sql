CREATE TABLE item_ids (id INTEGER PRIMARY KEY AUTOINCREMENT, dumb INTEGER DEFAULT 0)
CREATE TRIGGER after_insert_on_items AFTER INSERT ON items FOR EACH ROW
BEGIN
    INSERT INTO item_ids (dumb) VALUES (0);
    UPDATE items SET id = last_insert_rowid() WHERE id=NEW.id;
END

INSERT INTO items (title) VALUES ('test')


