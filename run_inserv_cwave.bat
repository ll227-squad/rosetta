TITLE Run cwave inserv *** DO NOT FORCE QUIT ***
:: A is the main computer (this computer), ssh client
:: B is the cwave_control computer (NUC unit on top of C-WAVE), ssh server
:: A2, B2 is for the wavelength meter files (was running out of variable names...)
set INSERVFILE=inserv_cwave.py
set DRIVERFILE1=gtr.py
set DRIVERFILE2=gtr_wrapper.py
set DRIVERFILE3=WS8.py
set DRIVERFILE4=wlmConst.py
set DRIVERFILE5=wlmData.dll
set DRIVERFILE6=wlmData.py
set INSERVPATHA=C:\Users\awsch\rosetta\src\rosetta
set DRIVERPATHA=C:\Users\awsch\rosetta\src\rosetta\drivers\hubner
set DRIVERPATHA2=C:\Users\awsch\rosetta\src\rosetta\drivers\highfinesse
set INSERVPATHB=C:\Users\cwave_control\cwave
set DRIVERPATHB=C:\Users\cwave_control\cwave\drivers\hubner
set DRIVERPATHB2=C:\Users\cwave_control\cwave\drivers\highfinesse
set USERNAMEB=cwave_control
set IPB=192.168.1.95
set CONDAPATHB=C:\Users\cwave_control\miniconda3
set ENVNAMEB=nsp
ECHO ========================================================================================
ECHO =========================== COPY FILES TO CWAVE_CONTROL ================================
ECHO ========================================================================================
ECHO Copying file %INSERVFILE%.py over to cwave_control computer
:: Copy inserv_cwave file from this computer to cwave_control computer
call scp %INSERVPATHA%\%INSERVFILE% %USERNAMEB%@%IPB%:%INSERVPATHB%
ECHO Copying files %DRIVERFILE1%.py and %DRIVERFILE2%.py over to cwave_control computer
:: Copy driver files from this computer to cwave_control computer
call scp %DRIVERPATHA%\%DRIVERFILE1% %USERNAMEB%@%IPB%:%DRIVERPATHB%
:: Copy driver files from this computer to cwave_control computer
call scp %DRIVERPATHA%\%DRIVERFILE2% %USERNAMEB%@%IPB%:%DRIVERPATHB%
ECHO Copying files %DRIVERFILE3%.py, %DRIVERFILE4%.py, %DRIVERFILE5%.py,and %DRIVERFILE6%.py over to cwave_control computer
:: Copy driver files from this computer to cwave_control computer
call scp %DRIVERPATHA2%\%DRIVERFILE3% %USERNAMEB%@%IPB%:%DRIVERPATHB2%
:: Copy driver files from this computer to cwave_control computer
call scp %DRIVERPATHA2%\%DRIVERFILE4% %USERNAMEB%@%IPB%:%DRIVERPATHB2%
:: Copy driver files from this computer to cwave_control computer
call scp %DRIVERPATHA2%\%DRIVERFILE5% %USERNAMEB%@%IPB%:%DRIVERPATHB2%
:: Copy driver files from this computer to cwave_control computer
call scp %DRIVERPATHA2%\%DRIVERFILE6% %USERNAMEB%@%IPB%:%DRIVERPATHB2%
ECHO ========================================================================================
ECHO ========================================================================================
ECHO Creating a SSH tunnel to the CWAVE laptop
call ssh %USERNAMEB%@%IPB% -L :42067:127.0.0.1:42057 %INSERVPATHB%\run_inserv.bat
PAUSE