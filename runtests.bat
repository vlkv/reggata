call reggata_set_env.bat
set PATH=%PYTHON_HOME%;%PYTHON_HOME%\Lib\site-packages\PyQt4;%PYTHON_HOME%\Lib\site-packages\PyQt4\bin;c:\WINDOWS\system32;c:\WINDOWS;c:\WINDOWS\system32\wbem;
set PYTHONPATH=.\ui;.\lib;.\src

python .\tests\runtests.py .\tests\testrepo.rgt .\tests\testrepocopy.rgt

pause