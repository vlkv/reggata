rem Change PYTHON_HOME value according to configuration of your system
set PYTHON_HOME=c:\usr\Python-3.2.2

set PATH=%PYTHON_HOME%;%PYTHON_HOME%\Lib\site-packages\PyQt4;%PYTHON_HOME%\Lib\site-packages\PyQt4\bin;c:\WINDOWS;c:\WINDOWS\system32;c:\WINDOWS\system32\wbem;%PATH%

set PYTHONPATH=%CD%\..;%CD%\..\reggata

python ../reggata/tests/runtests.py
pause