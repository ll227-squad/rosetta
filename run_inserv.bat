@ECHO OFF
:: Run nspyre inserv with this file
TITLE Run inserv
set CONDAPATH=C:\Users\awsch\miniconda3
set ENVNAME=nsp
set INSERVPATH=C:\Users\awsch\rosetta\src\rosetta
set INSERVFILE=inserv_primary.py
ECHO ========================================================================
ECHO ========================================================================
ECHO Opening instrument server in %ENVNAME% environment
ECHO ========================================================================
ECHO ========================================================================
ECHO Trying to activate %ENVNAME% environment
ECHO ====================================
if %ENVNAME%==base (set ENVPATH=%CONDAPATH%) else (set ENVPATH=%CONDAPATH%\envs\%ENVNAME%)
call %CONDAPATH%\Scripts\activate.bat %ENVPATH%
ECHO %ENVNAME% environment activated
ECHO ====================================
ECHO Trying to open instrument server file %INSERVFILE% at %INSERVPATH%
ECHO ====================================
call python %INSERVPATH%\%INSERVFILE% 
PAUSE