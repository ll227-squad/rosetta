"""
Basic driver for HighFinesse Wavemeter WS-8.


Author: Michael Solomon, Jose Mendez
Date: 04/03/2024
"""

import ctypes
import sys

import wlmData
import wlmConst

DLL_PATH = "wlmData.dll"
# Load DLL from DLL_PATH
try:
    wlmData.LoadDLL(DLL_PATH)
except Exception:
    sys.exit("Error: Couldn't find DLL on path %s. Please check the DLL_PATH variable!" % DLL_PATH)


class WS8:
    def __init__(self):
        # Checks the number of WLM server instance(s)
        if wlmData.dll.GetWLMCount(0) == 0:
            print("There is no running wlmServer instance(s).")
        else:
            # Read Type, Version, Revision and Build number
            self.version_type = wlmData.dll.GetWLMVersion(0)
            self.version_ver = wlmData.dll.GetWLMVersion(1)
            self.version_rev = wlmData.dll.GetWLMVersion(2)
            self.version_build = wlmData.dll.GetWLMVersion(3)
            self.version = '%s.%s.%s.%s' % (self.version_type, self.version_ver, self.version_rev, self.version_build)
        self.dll = wlmData.dll
        self._signal1 = WS8signal(wlmData.dll, 1)
        self._signal2 = WS8signal(wlmData.dll, 2)
        self._signal3 = WS8signal(wlmData.dll, 3)
        self._signal4 = WS8signal(wlmData.dll, 4)
        self._signal5 = WS8signal(wlmData.dll, 5)
        self._signal6 = WS8signal(wlmData.dll, 6)
        self._signal7 = WS8signal(wlmData.dll, 7)
        self._signal8 = WS8signal(wlmData.dll, 8)

    @property
    def signal1(self) -> 'WS8signal':
        return self._signal1

    @property
    def signal2(self) -> 'WS8signal':
        return self._signal2

    @property
    def signal3(self) -> 'WS8signal':
        return self._signal3

    @property
    def signal4(self) -> 'WS8signal':
        return self._signal4

    @property
    def signal5(self) -> 'WS8signal':
        return self._signal5

    @property
    def signal6(self) -> 'WS8signal':
        return self._signal6

    @property
    def signal7(self) -> 'WS8signal':
        return self._signal7

    @property
    def signal8(self) -> 'WS8signal':
        return self._signal8

    @property
    def laser_PID_enable(self) -> bool:
        return self.dll.GetDeviationMode(0)

    @laser_PID_enable.setter
    def laser_PID_enable(self, active: bool) -> None:
        self.dll.SetDeviationMode(active)

    def __exit__(self):
        self.laser_PID_enable = False


class WS8signal:

    def __init__(self, dll, signal_port):
        self.__dll = dll
        self.__port = signal_port
        self._dPID = WS8dPID(dll, self.__port)

    @property
    def dPID(self) -> 'WS8dPID':
        return self._dPID

    @property
    def frequency(self) -> (str, float):
        """Returns the frequency in THz."""
        # Read frequency
        freq = self.__dll.GetFrequencyNum(self.__port, 0)
        if freq == wlmConst.ErrWlmMissing:
            status_string = 'WLM inactive'
        elif freq == wlmConst.ErrNoSignal:
            status_string = 'No Signal'
        elif freq == wlmConst.ErrBadSignal:
            status_string = 'Bad Signal'
        elif freq == wlmConst.ErrLowSignal:
            status_string = 'Low Signal'
        elif freq == wlmConst.ErrBigSignal:
            status_string = 'High Signal'
        elif freq == wlmConst.ErrOutOfRange:
            status_string = 'Ch{} Error: Out of Range'.format(self.__port)
        elif freq <= 0:
            status_string = 'Ch{} Error code: {}'.format(self.__port, freq)
        else:
            status_string = 'WLM is running'

        return status_string, freq

    @property
    def wavelength(self) -> float:
        """Returns the wavelength in nm."""
        # Read wavelength
        wavelength = self.__dll.GetWavelengthNum(self.__port, 0)
        status_string = None
        return wavelength
    
    @property
    def power(self) -> float:
        """Returns the power in uW (CW) or uJ (quasi CW)."""
        power = self.__dll.GetPowerNum(self.__port, 0)
        status_string = None
        return power

    @property
    def exposure_mode(self) -> bool:
        return self.__dll.GetExposureModeNum(self.__port, 0)

    @exposure_mode.setter
    def exposure_mode(self, mode: bool) -> None:
        self.__dll.SetExposureModeNum(self.__port, mode)

    @property
    def exposure(self) -> float:
        return self.__dll.GetExposureNum(self.__port, 1, 0)

    @exposure.setter
    def exposure(self, val: float) -> None:
        # val in miliseconds
        self.__dll.SetExposureNum(self.__port, 1, val)

    #self.dll.GetLinewidthNum
    #self.dll.GetExposureNum
    #self.dll.SetExposureNum


class WS8dPID:
    
    def __init__(self, dll, signal_port):
        self.__dll = dll
        self.__port = signal_port
    
#    @property
#    def port(self) -> int:
#        return self.__dll.GetLaserControlSetting(self)
#    
#    @port.setter
#    def port(self, laser_port: int) -> None:
#        iVal, dVal, sVal = ctypes.c_long(), ctypes.double(), ctypes.create_string_buffer(0)
#        self.__dll.SetLaserControlSetting(wlmConst.cmiDeviationRefMid, 2, iVal, dVal, sVal)
    
    @property
    def regulation_course(self) -> float:
        regulation = ctypes.create_string_buffer(1024)
        status = self.__dll.GetPIDCourseNum(self.__port, regulation)
        if status == wlmConst.ResERR_NoErr:
            return regulation.value
        elif status == wlmConst.ResERR_WlmMissing:
            None
        elif status == wlmConst.ResERR_ParmOutOfRange:
            None
    
    @regulation_course.setter
    def regulation_course(self, regulation: int) -> None:
        regulation = ctypes.c_char_p(str(regulation).encode('UTF-8'))
        self.__dll.SetPIDCourseNum(self.__port, regulation)
    
    @property
    def regulation(self) -> float:
        regulation = ctypes.create_string_buffer(1024)
        status = self.__dll.GetDeviationReference(0)
        if status == wlmConst.ResERR_NoErr:
            return regulation.value
        elif status == wlmConst.ResERR_WlmMissing:
            None
        elif status == wlmConst.ResERR_ParmOutOfRange:
            None
    