TITLE Run cwave inserv *** DO NOT FORCE QUIT ***
:: A is the main computer (this computer), ssh client
:: B is the laptop, ssh server
set INSERVFILE=inserv_cwave.py
set DRIVERFILE1=gtr_wrapper.py
set DRIVERFILE2=gtr.py
set INSERVPATHA=C:\Users\awsch\rosetta\src\rosetta
set DRIVERPATHA=C:\Users\awsch\rosetta\src\rosetta\drivers\hubner
set INSERVPATHB=C:\Users\Awsch\cwave
set DRIVERPATHB=C:\Users\Awsch\cwave\drivers\hubner
set USERNAMEB=Awsch
set IPB=192.168.1.95
set CONDAPATHB=C:\Users\Awsch\miniconda3
set ENVNAMEB=nsp
ECHO ========================================================================================
ECHO ========================================================================================
ECHO Copying files (%INSERVFILE%.py, %DRIVERFILE1%.py, and %DRIVERFILE2%.py) over to laptop
:: Copy inserv_cwave file from this computer to laptop
call scp %INSERVPATHA%\%INSERVFILE% %USERNAMEB%@%IPB%:%INSERVPATHB%
:: Copy driver files from this computer to laptop
call scp %DRIVERPATHA%\%DRIVERFILE1% %USERNAMEB%@%IPB%:%DRIVERPATHB%
:: Copy driver files from this computer to laptop
call scp %DRIVERPATHA%\%DRIVERFILE2% %USERNAMEB%@%IPB%:%DRIVERPATHB%
:: Start inserv_cwave on laptop; this is the critical command
ECHO ========================================================================================
ECHO ========================================================================================
ECHO Creating a SSH tunnel to the CWAVE laptop
call ssh %USERNAMEB%@%IPB% -L :42067:127.0.0.1:42057 %INSERVPATHB%\run_inserv.bat
PAUSE