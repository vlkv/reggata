import os
from reggata import consts


logFilePath = os.path.join(consts.USER_CONFIG_DIR, "reggata.log")

loggingDefaultConf = \
'''
[loggers]
keys=root,reggata,sqlalchemy_engine

[handlers]
keys=defaultHandler

[formatters]
keys=defaultFormatter





[logger_root]
level=DEBUG
handlers=defaultHandler

[logger_reggata]
level=DEBUG
handlers=defaultHandler
qualname=reggata
propagate=0

[logger_sqlalchemy_engine]
level=WARNING
handlers=defaultHandler
qualname=sqlalchemy.engine
propagate=0



[handler_defaultHandler]
class=FileHandler
level=DEBUG
formatter=defaultFormatter
args=(r"{logFilePath}", "w", "utf-8")



[formatter_defaultFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
datefmt=
'''.format(**{"logFilePath": logFilePath})
