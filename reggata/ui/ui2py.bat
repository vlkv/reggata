set PYTHON_HOME=c:\usr\Python-3.3.0
%PYTHON_HOME%\Lib\site-packages\PyQt4\pyuic4 --from-imports %1 > "ui_"%~n1".py" 
