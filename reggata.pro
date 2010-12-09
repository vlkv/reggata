FORMS += ui/itemdialog.ui
FORMS += ui/itemsdialog.ui
FORMS += ui/mainwindow.ui
FORMS += ui/userdialog.ui
SOURCES += src/consts.py \
	src/db_schema.py \
	src/exceptions.py \
	src/ext_app_mgr.py \
	src/helpers.py \
	src/item_dialog.py \
	src/items_dialog.py \
	src/main_window.py \
	src/repo_mgr.py \
	src/tag_cloud.py \
	src/user_config.py \
	src/user_dialog.py \
	src/parsers/fields_def_parser.py \
	src/parsers/fields_def_tokens.py \
	src/parsers/query_parser.py \
	src/parsers/query_tokens.py \
	src/parsers/query_tree_nodes.py \
	src/parsers/tags_def_parser.py \
	src/parsers/tags_def_tokens.py \
	src/parsers/util.py
TRANSLATIONS += reggata_ru.ts
