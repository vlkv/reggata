rem Change PYTHON_HOME and GIT_BIN values according to configuration of your system
set PYTHON_HOME=c:\usr\Python-3.2.2
set GIT_BIN=c:\usr\Git\bin

set PATH=%PYTHON_HOME%;%PYTHON_HOME%\Lib\site-packages\PyQt4;%PYTHON_HOME%\Lib\site-packages\PyQt4\bin;c:\WINDOWS;c:\WINDOWS\system32;c:\WINDOWS\system32\wbem;%PATH%

rem %GIT_BIN%\git describe --tags master > ..\version.txt
%GIT_BIN%\git log -1 > ..\git_version.txt
mkdir ..\binary_builds
python ..\cx_setup.py build > .\build_out.log 2>&1
pause
