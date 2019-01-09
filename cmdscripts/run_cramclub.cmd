rem @echo off
setlocal
set CWD=%~dp0
rem echo CWD %CWD%
set PY=C:\Users\chris.kerle\AppData\Local\Programs\Python\Python37-32\python.exe 
"%PY%" "%CWD%..\cramclub\cramclub.py" --loglevel WARNING start --instance %1 %2 %3 %4 %5 %6 %7 %8 %9
endlocal