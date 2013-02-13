import os
from reggata import consts

if not os.path.exists(consts.USER_CONFIG_DIR):
        os.makedirs(consts.USER_CONFIG_DIR)
