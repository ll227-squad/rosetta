@ECHO OFF
:: Run nspyre dataserv with this file
TITLE Run dataserv
set CONDAPATH=C:\Users\awsch\miniconda3
set ENVNAME=nsp
set DATSERVPATH=C:\Users\awsch\rosetta\src\rosetta
set DATASERVCMD=nspyre-dataserv
ECHO ========================================================================
ECHO ========================================================================
ECHO Opening data server in %ENVNAME% environment
ECHO ========================================================================
ECHO ========================================================================
if %ENVNAME%==base (set ENVPATH=%CONDAPATH%) else (set ENVPATH=%CONDAPATH%\envs\%ENVNAME%)
call %CONDAPATH%\Scripts\activate.bat %ENVPATH%
ECHO %ENVNAME% environment activated
ECHO ====================================
ECHO Trying to open data server at %DATSERVPATH%
ECHO ====================================
call nspyre-dataserv
PAUSE