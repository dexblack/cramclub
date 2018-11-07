@echo off
setlocal
set cwd=%~dp0
pushd %cwd%
call env\Scripts\activate.bat
python cramclub.py start -i test
popd
endlocal
pause