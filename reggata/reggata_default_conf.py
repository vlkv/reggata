import sys

_minimalReggataConf ='''
#####################################################################
# This is a Reggata confguration file ~/.config/reggata/reggata.conf
#####################################################################

main_window.width=920
main_window.height=683
main_window.state=b'\\x00\\x00\\x00\\xff\\x00\\x00\\x00\\x00\\xfd\\x00\\x00\\x00\\x01\\x00\\x00\\x00\\x02\\x00\\x00\\x03\\x98\\x00\\x00\\x02\\x81\\xfc\\x01\\x00\\x00\\x00\\x01\\xfc\\x00\\x00\\x00\\x00\\x00\\x00\\x03\\x98\\x00\\x00\\x02\\x04\\x00\\xff\\xff\\xff\\xfc\\x02\\x00\\x00\\x00\\x02\\xfb\\x00\\x00\\x00,\\x00T\\x00a\\x00g\\x00C\\x00l\\x00o\\x00u\\x00d\\x00T\\x00o\\x00o\\x00l\\x00D\\x00o\\x00c\\x00k\\x00W\\x00i\\x00d\\x00g\\x00e\\x00t\\x01\\x00\\x00\\x00\\x15\\x00\\x00\\x00\\x8e\\x00\\x00\\x00i\\x00\\xff\\xff\\xff\\xfc\\x00\\x00\\x00\\xa9\\x00\\x00\\x01\\xed\\x00\\x00\\x00\\xaa\\x01\\x00\\x00\\x14\\xfa\\x00\\x00\\x00\\x01\\x01\\x00\\x00\\x00\\x02\\xfb\\x00\\x00\\x002\\x00F\\x00i\\x00l\\x00e\\x00B\\x00r\\x00o\\x00w\\x00s\\x00e\\x00r\\x00T\\x00o\\x00o\\x00l\\x00D\\x00o\\x00c\\x00k\\x00W\\x00i\\x00d\\x00g\\x00e\\x00t\\x01\\x00\\x00\\x00\\x00\\xff\\xff\\xff\\xff\\x00\\x00\\x00U\\x00\\xff\\xff\\xff\\xfb\\x00\\x00\\x000\\x00I\\x00t\\x00e\\x00m\\x00s\\x00T\\x00a\\x00b\\x00l\\x00e\\x00T\\x00o\\x00o\\x00l\\x00D\\x00o\\x00c\\x00k\\x00W\\x00i\\x00d\\x00g\\x00e\\x00t\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x03\\x98\\x00\\x00\\x02\\x04\\x00\\xff\\xff\\xff\\x00\\x00\\x03\\x98\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x04\\x00\\x00\\x00\\x04\\x00\\x00\\x00\\x08\\x00\\x00\\x00\\x08\\xfc\\x00\\x00\\x00\\x00'

tag_cloud.height=143
tag_cloud.width=920
tag_cloud.dock_area=4
tag_cloud.tag_background_color = Beige
tag_cloud.limit=100

spinBox_limit.value = 50
spinBox_limit.page = 1

thumbnail_size = 100

recent_user.login=user
recent_user.password=12dea96fec20593566ab75692c9949596833adc9

language = en

sqlalchemy.engine_echo = False

'''

_confTemplate = \
'''
tmp_dir = {TMP_DIR}

# Commands for invoking external applications.
# %f will be replaced with absolute file name (of selected item)
# %d will be replaced with absolute path to containing directory (of selected item)
# If path to command contains spaces, surround it with double quotes,
# for example:
# ext_app_mgr.audio.command="C:\Program Files\K-Lite Codec Pack\Media Player Classic\mplayerc.exe" %f
# ext_app_mgr.audio.command=vlc %f
ext_app_mgr_file_types=['images', 'pdf', 'audio', 'plain_text']

ext_app_mgr.images.extensions=['.jpg', '.png', '.gif', '.bmp']
ext_app_mgr.images.command={IMAGE_VIEWER} %f

ext_app_mgr.pdf.extensions=['.pdf']
ext_app_mgr.pdf.command={PDF_VIEWER} %f

ext_app_mgr.audio.extensions=['.mp3', '.ogg', '.flac', '.wav', '.m3u']
ext_app_mgr.audio.command={AUDIO_PLAYER} %f

ext_app_mgr.plain_text.extensions=['.txt', '.csv']
ext_app_mgr.plain_text.command={TEXT_EDITOR} %f

# Command for invoking external file manager program
# %f will be replaced with absolute file name (of selected item)
# %d will be replaced with absolute path to containing directory (of selected item)
# If path to command contains spaces, surround it with double quotes
ext_file_manager={EXTERNAL_FILE_MANAGER} %d

'''

reggataDefaultConf = _minimalReggataConf

if sys.platform.startswith("win"):
    reggataDefaultConf += _confTemplate.format(
        IMAGE_VIEWER = '''"c:\WINDOWS\system32\mspaint.exe"''',
        PDF_VIEWER = '''"c:\Program Files\SumatraPDF.exe"''',
        AUDIO_PLAYER = '''"c:\Program Files\K-Lite Codec Pack\Media Player Classic\mplayerc.exe"''',
        TEXT_EDITOR = '''"c:\WINDOWS\\notepad.exe"''',
        EXTERNAL_FILE_MANAGER = '''"c:\WINDOWS\explorer.exe"''',
        TMP_DIR = '''"C:\Temp"''')

elif sys.platform.startswith("linux"):
    reggataDefaultConf += _confTemplate.format(
        IMAGE_VIEWER = '''gqview''',
        PDF_VIEWER = '''xpdf''',
        AUDIO_PLAYER = '''vlc''',
        TEXT_EDITOR = '''xedit''',
        EXTERNAL_FILE_MANAGER = '''xfm''',
        TMP_DIR = '''/tmp''')

