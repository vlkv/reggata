
reggataDefaultConf = \
'''
# This is a Reggata confguration file ~/.config/reggata/reggata.conf 
#
#

main_window.width=920
main_window.height=683

tag_cloud.height=143
tag_cloud.width=920
tag_cloud.dock_area=4
tag_cloud.tag_background_color = Beige
tag_cloud.limit=100

spinBox_limit.value = 50
spinBox_limit.page = 1

recent_repo.base_path=/home/vlkv/_reggata_test_repo/
recent_user.login=vlkv
recent_user.password=da39a3ee5e6b4b0d3255bfef95601890afd80709


#Commands for invoking external applications.
# %f will be replaced with absolute file name (of selected item)
# %d will be replaced with absolute path to containing directory (of selected item)
# If path to command contains spaces, surround it with double quotes, 
# for example:
# ext_app_mgr.audio.command="C:\Program Files\K-Lite Codec Pack\Media Player Classic\mplayerc.exe" %f
ext_app_mgr_file_types=['images', 'pdf', 'audio', 'plain_text']

ext_app_mgr.images.extensions=['.jpg', '.png', '.gif', '.bmp']
ext_app_mgr.images.command="c:\WINDOWS\system32\mspaint.exe" %f

ext_app_mgr.pdf.extensions=['.pdf']
ext_app_mgr.pdf.command="c:\Program Files\SumatraPDF.exe" %f

ext_app_mgr.audio.extensions=['.mp3', '.ogg', '.flac', '.wav', '.m3u']
ext_app_mgr.audio.command="c:\Program Files\K-Lite Codec Pack\Media Player Classic\mplayerc.exe" %f

ext_app_mgr.plain_text.extensions=['.txt']
ext_app_mgr.plain_text.command="c:\WINDOWS\\notepad.exe" %f

#Command for invoking external file manager program
# %f will be replaced with absolute file name (of selected item)
# %d will be replaced with absolute path to containing directory (of selected item)
# If path to command contains spaces, surround it with double quotes
ext_file_manager="c:\WINDOWS\explorer.exe" %d

language = en

sqlalchemy.engine_echo = False

thumbnail_size = 100


# Default tmp dir is located here ~/.config/reggata/tmp
# Uncomment only if you want different location of tmp directory
#tmp_dir = "C:\tmp"


#Field with this name will be used by Reggata to store item's rating.
reserved_fields.rating = Rating

#Field with this name will be used by Reggata to store item's notes and comments.
reserved_fields.notes = Notes

'''



