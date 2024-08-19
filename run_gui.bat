@ECHO OFF
:: Run nspyre gui with this file
TITLE Run dataserv
set CONDAPATH=C:\Users\awsch\miniconda3
set ENVNAME=nsp
set GUIPATH=C:\Users\awsch\rosetta\src\rosetta\gui
set GUIFILE=app.py
ECHO ========================================================================
ECHO ========================================================================
ECHO Opening gui in %ENVNAME% environment
ECHO ========================================================================
ECHO ========================================================================
ECHO Trying to activate %ENVNAME% environment
ECHO ====================================
if %ENVNAME%==base (set ENVPATH=%CONDAPATH%) else (set ENVPATH=%CONDAPATH%\envs\%ENVNAME%)
call %CONDAPATH%\Scripts\activate.bat %ENVPATH%
ECHO %ENVNAME% environment activated
ECHO ====================================
ECHO Trying to open gui file %GUIFILE% at %GUIPATH%
ECHO ====================================
call python %GUIPATH%\%GUIFILE% 
PAUSE