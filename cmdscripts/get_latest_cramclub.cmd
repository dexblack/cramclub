@echo off
setlocal
echo Running %~n0 from %~dp0
pushd %~dp0..
git checkout master
git pull
popd
endlocal
pause