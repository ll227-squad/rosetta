'''This module allows control of the Hubner C-WAVE GTR Laser.'''

# pylint: disable=R0904

import threading
import base64
import struct
import typing
import enum
import json
import asyncio
import websockets

class _Reader:
    '''Helper class for reading binary values from an array'''
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def read(self, length: int):
        '''Reads number of bytes from array'''
        assert isinstance(length, int)
        if self.pos + length > len(self.data):
            raise ValueError('Buffer end reached')
        data = self.data[self.pos:self.pos+length]
        self.pos += length
        return data

    def get_int8(self):
        '''Reads a int8'''
        return int.from_bytes(self.read(1), signed=True, byteorder='little')

    def get_uint8(self):
        '''Reads a uint8'''
        return int.from_bytes(self.read(1), signed=False, byteorder='little')

    def get_int32(self):
        '''Reads a int32'''
        return int.from_bytes(self.read(4), signed=True, byteorder='little')

    def get_uint32(self):
        '''Reads a uint32'''
        return int.from_bytes(self.read(4), signed=False, byteorder='little')

    def get_int64(self):
        '''Reads a int64'''
        return int.from_bytes(self.read(8), signed=True, byteorder='little')

    def get_uint64(self):
        '''Reads a uint64'''
        return int.from_bytes(self.read(8), signed=False, byteorder='little')

    def get_double(self):
        '''Reads a double'''
        return struct.unpack('d', bytes(self.read(8)))[0]

class Info(typing.NamedTuple):
    '''Represents info structure'''
    name: str
    version: str
    revision: int
    serialNumber: int
    mac: str

class StatusBits(typing.NamedTuple):
    '''Represents the status bits of the device'''
    @classmethod
    def from_reader(cls, reader: _Reader):
        '''Contructs an object from a reader'''
        assert isinstance(reader, _Reader)
        raw_value = reader.get_uint32()
        return StatusBits(
            bool(raw_value & (1<<0)),
            bool(raw_value & (1<<1)),
            bool(raw_value & (1<<2)),
            bool(raw_value & (1<<3)),
            bool(raw_value & (1<<4)),
            bool(raw_value & (1<<5)),
            bool(raw_value & (1<<6)),
            bool(raw_value & (1<<7)),
            bool(raw_value & (1<<8)),
            bool(raw_value & (1<<16)),
            bool(raw_value & (1<<17)),
            bool(raw_value & (1<<18)),
            bool(raw_value & (1<<19)),
            bool(raw_value & (1<<20)),
            bool(raw_value & (1<<24)),
            bool(raw_value & (1<<25)),
        )

    tempOpo: bool
    tempShg: bool
    tempRef: bool
    lockOpo: bool
    lockShg: bool
    lockEtalon: bool
    pumpPower: bool
    shgRequested: bool
    useWlmForShg: bool
    guardOpoPosition: bool
    tecHardwareEnable: bool
    shgPdhEnabled: bool
    wlmConnected: bool
    wlmWarning: bool
    hasWlmDialLicense: bool
    hasWlmStabilizeLicense: bool

class AllowedActionBits(typing.NamedTuple):
    '''Represents which actions are currently allowed to be executed.'''
    @classmethod
    def from_reader(cls, reader: _Reader):
        '''Contructs an object from a reader'''
        assert isinstance(reader, _Reader)
        raw_value = reader.get_uint32()
        return AllowedActionBits(
            bool(raw_value & (1<<0)),
            bool(raw_value & (1<<1)),
            bool(raw_value & (1<<2)),
            bool(raw_value & (1<<3)),
            bool(raw_value & (1<<4)),
            bool(raw_value & (1<<5)),
        )

    dial: bool
    lyotOptimization: bool
    etalonOptimization: bool
    referenceCalibration: bool
    opoTemperatureOptimization: bool
    shgTemperatureOptimization: bool

class MappingFieldChannel(enum.Enum):
    '''Enumeration of mapping field channels'''
    XtalOpo = 'xtalOpo'
    XtalShg = 'xtalShg'
    Lyot = 'lyot'

class ScanStep(typing.NamedTuple):
    '''Configuration for temperature scan step'''
    range: float
    slewRate: float

class TemperatureOptimizeChannel(enum.Enum):
    '''Enumeration of temperature optimization channels'''
    Opo = 'opo'
    Shg = 'shg'

class ShutterChannel(enum.Enum):
    '''Enumeration of shutter channels'''
    LaserOut = 'laserOut'
    OpoOut = 'opoOut'
    ShgOut = 'shgOut'
    Pump = 'pump'
    MirOut = 'mirOut'

class TecChannel(enum.Enum):
    '''Enumeration of TEC channels'''
    Opo = 'opo'
    Shg = 'shg'
    Ref = 'ref'

class PiezoMode(enum.Enum):
    '''Enumeration of piezo modes'''
    Manual = 'manual'
    Scan = 'scan'
    Control = 'control'

    @classmethod
    def from_reader(cls, reader: _Reader):
        '''Contructs an object from a reader'''
        assert isinstance(reader, _Reader)
        return list(cls)[reader.get_uint8()]

class PiezoControlSource(enum.Enum):
    '''Enumeration of piezo control sources'''
    Non = 'none'
    Pump = 'pump'
    Opo = 'opo'
    Shg = 'shg'
    ShgPdh = 'shgPdh'
    Ref = 'ref'
    Ref_Bal = 'refBal'
    Aux = 'aux'

    @classmethod
    def from_reader(cls, reader: _Reader):
        '''Contructs an object from a reader'''
        assert isinstance(reader, _Reader)
        # index starts at -1 for None
        return list(cls)[reader.get_int8()+1]

class PiezoChannel(enum.Enum):
    '''Enumeration of piezo channels'''
    Opo = 'opo'
    Shg = 'shg'
    Etalon = 'etalon'
    Ref = 'ref'

class PiezoScanSettings(typing.NamedTuple):
    '''Piezo settings in scan mode'''
    min: float
    max: float
    rate: float

class StepperChannel(enum.Enum):
    '''Enumeration of stepper channels'''
    Opo = 'opo'
    Shg = 'shg'

class ScanChannel(enum.Enum):
    '''Enumeration of scan channels'''
    TemperatureOpo = 'tempOpo'
    TemperatureShg = 'tempShg'
    PiezoEtalon = 'piezoEtalon'
    Lyot = 'lyot'

class OpoState(enum.Enum):
    '''Enumeration of OPO statemachine states'''
    Idle = 0
    StartDial = 1
    WaitForPump = 2
    ScanLyot = 3
    ScanTemperature = 4
    OptimizeEtalon = 5
    CalibrateReference = 6
    Stabilize = 7
    StabilizeWlm = 8

class ShgState(enum.Enum):
    '''Enumeration of SHG statemachine states'''
    Idle = 0
    StartDial = 1
    WaitForOpo = 2
    WaitForWlm = 3
    ScanTemperature = 4
    Stabilize = 5

class MonitorSource(enum.Enum):
    '''Enumeration of monitor sources'''
    PdPump = 'pdPump'
    PdOpo = 'pdOpo'
    PdShgPdh = 'pdShgPdh'
    PdRef = 'pdRef'
    PdShg = 'pdShg'
    PdEtalon = 'pdEtalon'
    LockinAverage = 'lockinAverage'
    OutOpo = 'outOpo'
    OutShg = 'outShg'
    OutEtalon = 'outEtalon'
    RefBalanced = 'refBalanced'
    Aux = 'aux'
    OutRef = 'outRef'

    @classmethod
    def from_reader(cls, reader: _Reader):
        '''Contructs an object from a reader'''
        assert isinstance(reader, _Reader)
        return list(cls)[reader.get_uint8()]

class TriggerSource(enum.Enum):
    '''Enumeration of trigger sources'''
    Opo = 'opo'
    Shg = 'shg'
    Etalon = 'etalon'
    Ref = 'ref'
    HomingOpo = 'homingOpo'
    HomingShg = 'homingShg'

    @classmethod
    def from_reader(cls, reader: _Reader):
        '''Contructs an object from a reader'''
        assert isinstance(reader, _Reader)
        return list(cls)[reader.get_uint8()]

class StatusDataPiezo(typing.NamedTuple):
    '''Represents status data of a piezo'''
    mode: PiezoMode
    setpoint: float
    manualOutput: float
    scanMin: float
    scanMax: float
    scanRate: float
    error: float
    input: float
    output: float
    enabled: bool
    slewRate: float
    invert: bool
    inputSource: PiezoControlSource
    criterionSource: PiezoControlSource
    threshold: float
    searchRate: float
    kP: int
    kI: int
    kD: int

    @classmethod
    def from_reader(cls, reader: _Reader):
        '''Contructs an object from a reader'''
        assert isinstance(reader, _Reader)
        return StatusDataPiezo(
            mode=PiezoMode.from_reader(reader),
            setpoint=reader.get_double(),
            manualOutput=reader.get_double(),
            scanMin=reader.get_double(),
            scanMax=reader.get_double(),
            scanRate=reader.get_double(),
            error=reader.get_double(),
            input=reader.get_double(),
            output=reader.get_double(),
            enabled=reader.get_uint8() != 0,
            slewRate=reader.get_double(),
            invert=reader.get_uint8() != 0,
            inputSource=PiezoControlSource.from_reader(reader),
            criterionSource=PiezoControlSource.from_reader(reader),
            threshold=reader.get_double(),
            searchRate=reader.get_double(),
            kP=reader.get_uint32(),
            kI=reader.get_uint32(),
            kD=reader.get_uint32()
        )

class ShutterState(enum.Enum):
    '''Enumeration of shutter states'''
    Closed = 0
    Open = 1
    Guarding = 2

    @classmethod
    def from_reader(cls, reader: _Reader):
        '''Contructs an object from a reader'''
        assert isinstance(reader, _Reader)
        return list(cls)[reader.get_uint8()]

class StepperHomingState(enum.Enum):
    '''Enumeration of stepper homing states'''
    Done = 0
    BladeOut = 1
    BladeEdge = 2
    BladeIn = 3
    BladeSlit = 4
    Unknown = 5
    Error = 6

    @classmethod
    def from_reader(cls, reader: _Reader):
        '''Contructs an object from a reader'''
        assert isinstance(reader, _Reader)
        return list(cls)[reader.get_uint8()]

class StatusDataStepper(typing.NamedTuple):
    '''Represents status data of a stepper'''
    position: int
    target: int
    isMoving: bool
    homingState: StepperHomingState
    targetPeriod: int
    isInactivePosition: bool
    frequency: float

    @classmethod
    def from_reader(cls, reader: _Reader):
        '''Contructs an object from a reader'''
        assert isinstance(reader, _Reader)
        return StatusDataStepper(
            position=reader.get_int32(),
            target=reader.get_int32(),
            isMoving=reader.get_uint8() != 0,
            homingState=StepperHomingState.from_reader(reader),
            targetPeriod=reader.get_int8(),
            isInactivePosition=reader.get_uint8() != 0,
            frequency=reader.get_double()
        )

class StatusDataTec(typing.NamedTuple):
    '''Represents status data of a TEC'''
    enabled: bool
    temperature: float
    setpoint: float
    output: float
    slewRate: float
    kP: int
    kI: int
    outMin: int
    outMax: int

    @classmethod
    def from_reader(cls, reader: _Reader):
        '''Contructs an object from a reader'''
        assert isinstance(reader, _Reader)
        return StatusDataTec(
            enabled=reader.get_uint8() != 0,
            temperature=reader.get_double(),
            setpoint=reader.get_double(),
            output=reader.get_double(),
            slewRate=reader.get_double(),
            kP=reader.get_uint32(),
            kI=reader.get_uint32(),
            outMin=reader.get_uint32(),
            outMax=reader.get_uint32()
        )

class StatusData(typing.NamedTuple):
    '''Containts all status data of the device.'''
    # ABI
    abiVersion: int
    # SYSTEM
    systemTime: int
    statusBits: StatusBits
    systemUptime: int
    operationTime: int
    targetWavelength: float
    measuredWavelength: float
    stateOpo: OpoState
    stateShg: ShgState
    allowedActionsBits: AllowedActionBits
    etaOpo: int
    etaShg: int
    # WLM
    wlmEnabled: bool
    wlmSetpoint: float
    wlmKp: float
    wlmKi: float
    # TEMPERATURES
    temperatureSoc: float
    temperatureBoard: float
    temperatureBaseplate: float
    temperatureCase: float
    # MONITOR
    monitor0Source: MonitorSource
    monitor1Source: MonitorSource
    # TRIGGER
    triggerSource: TriggerSource
    # PIEZOS
    piezoOpo: StatusDataPiezo
    piezoShg: StatusDataPiezo
    piezoEtalon: StatusDataPiezo
    piezoRef: StatusDataPiezo
    # LOCK-IN
    lockinAverage: float
    lockinMovingAverage: float
    lockinEnabled: bool
    lockinModDivisorBits: int
    lockinFrequency: int
    lockinPhase: int
    lockinAveragingBits: int
    lockinOutDivisorBits: int
    # SHUTTER
    shutterStateLaserOut: ShutterState
    shutterStateOpoOut: ShutterState
    shutterStateShgOut: ShutterState
    shutterStatePump: ShutterState
    shutterStateMirOut: ShutterState
    # STEPPERS
    stepperOpo: StatusDataStepper
    stepperShg: StatusDataStepper
    # LYOT
    lyotPosition: int
    lyotTarget: int
    lyotIsMoving: bool
    lyotIsInselective: int
    lyotFrequency: float
    # PHOTODIODES
    pdPumpFullScale: float
    pdPumpPower: float
    pdPumpScalingFactor: float
    pdOpoFullScale: float
    pdOpoPower: float
    pdOpoScalingFactor: float
    pdShgFullScale: float
    pdShgPower: float
    pdShgScalingFactor: float
    pdShgPdhFullScale: float
    pdShgPdhScalingFactor: float
    pdEtalonFullScale: float
    pdEtalonScalingFactor: float
    pdRefFullScale: float
    pdRefScalingFactor: float
    pdAuxFullScale: float
    pdAuxScalingFactor: float
    # TEC
    tecOpo: StatusDataTec
    tecShg: StatusDataTec
    tecRef: StatusDataTec

    @classmethod
    def from_reader(cls, reader: _Reader):
        '''Contructs an object from a reader'''
        return StatusData(
            abiVersion=reader.get_uint32(),
            systemTime=reader.get_uint64(),
            statusBits=StatusBits.from_reader(reader),
            systemUptime=reader.get_uint64(),
            operationTime=reader.get_uint64(),
            targetWavelength=reader.get_double(),
            measuredWavelength=reader.get_double(),
            stateOpo=OpoState(reader.get_uint8()),
            stateShg=ShgState(reader.get_uint8()),
            allowedActionsBits=AllowedActionBits.from_reader(reader),
            etaOpo=reader.get_int32(),
            etaShg=reader.get_int32(),
            wlmEnabled=reader.get_uint8() != 0,
            wlmSetpoint=reader.get_double(),
            wlmKp=reader.get_double(),
            wlmKi=reader.get_double(),
            temperatureSoc=reader.get_double(),
            temperatureBoard=reader.get_double(),
            temperatureBaseplate=reader.get_double(),
            temperatureCase=reader.get_double(),
            monitor0Source=MonitorSource.from_reader(reader),
            monitor1Source=MonitorSource.from_reader(reader),
            triggerSource=TriggerSource.from_reader(reader),
            piezoShg=StatusDataPiezo.from_reader(reader),
            piezoOpo=StatusDataPiezo.from_reader(reader),
            piezoEtalon=StatusDataPiezo.from_reader(reader),
            piezoRef=StatusDataPiezo.from_reader(reader),
            lockinAverage=reader.get_double(),
            lockinMovingAverage=reader.get_double(),
            lockinEnabled=reader.get_uint8() != 0,
            lockinModDivisorBits=reader.get_uint32(),
            lockinFrequency=reader.get_uint32(),
            lockinPhase=reader.get_uint32(),
            lockinAveragingBits=reader.get_uint32(),
            lockinOutDivisorBits=reader.get_uint32(),
            shutterStateLaserOut=ShutterState.from_reader(reader),
            shutterStateOpoOut=ShutterState.from_reader(reader),
            shutterStateShgOut=ShutterState.from_reader(reader),
            shutterStatePump=ShutterState.from_reader(reader),
            shutterStateMirOut=ShutterState.from_reader(reader),
            stepperOpo=StatusDataStepper.from_reader(reader),
            stepperShg=StatusDataStepper.from_reader(reader),
            lyotPosition=reader.get_int32(),
            lyotTarget=reader.get_int32(),
            lyotIsMoving=reader.get_uint8() != 0,
            lyotIsInselective=reader.get_uint8() != 0,
            lyotFrequency=reader.get_double(),
            pdPumpFullScale=reader.get_double(),
            pdPumpPower=reader.get_double(),
            pdPumpScalingFactor=reader.get_double(),
            pdOpoFullScale=reader.get_double(),
            pdOpoPower=reader.get_double(),
            pdOpoScalingFactor=reader.get_double(),
            pdShgFullScale=reader.get_double(),
            pdShgPower=reader.get_double(),
            pdShgScalingFactor=reader.get_double(),
            pdShgPdhFullScale=reader.get_double(),
            pdShgPdhScalingFactor=reader.get_double(),
            pdEtalonFullScale=reader.get_double(),
            pdEtalonScalingFactor=reader.get_double(),
            pdRefFullScale=reader.get_double(),
            pdRefScalingFactor=reader.get_double(),
            pdAuxFullScale=reader.get_double(),
            pdAuxScalingFactor=reader.get_double(),
            tecOpo=StatusDataTec.from_reader(reader),
            tecShg=StatusDataTec.from_reader(reader),
            tecRef=StatusDataTec.from_reader(reader)
        )

class Gtr:
    '''Represents a handle to the device.'''

    def __init__(self):
        self.ws_cmd = None
        # create a new event loop and run in seperate thread
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever)
        # this will stop the thread when application exits
        self.thread.daemon = True
        self.thread.start()
        self.lock = threading.Lock()

    async def __async__connect(self, address: str) -> None:
        assert isinstance(address, str)
        base_url = 'ws://' + address  + '/api'
        self.ws_cmd = await websockets.connect(base_url + '/cmd', ping_interval=None)

    async def __async__disconnect(self) -> None:
        if self.ws_cmd is None:
            return
        await self.ws_cmd.close()
        self.ws_cmd = None

    async def __async__query(self, query) -> dict:
        await self.ws_cmd.send(json.dumps(query))
        ret = await self.ws_cmd.recv()
        ret_json = json.loads(ret)
        if not isinstance(ret_json, dict):
            raise Exception("Query failed: " + str(ret))
        if ret_json["res"] != 'ok':
            raise Exception("Query failed: " + ret_json["arg"])
        return ret_json

    def __query(self, cmd: str, chan: str, type_: str, arg: any) -> dict:
        assert isinstance(cmd, str)
        assert isinstance(chan, str) or chan is None
        assert isinstance(type_, str)
        with self.lock:
            if self.ws_cmd is None:
                raise ConnectionError('Socket is not connected')
            query = {
                "uid": 0,
                "cmd": cmd,
                "chan": chan,
                "type": type_,
                "arg": arg,
            }
            return asyncio.run_coroutine_threadsafe(self.__async__query(query), self.loop).result()

    def __set(self, cmd: str, chan: str = None, arg: str = None) -> dict:
        return self.__query(cmd, chan, "set", arg)

    def __get(self, cmd: str, chan: str = None, arg: str = None) -> dict:
        return self.__query(cmd, chan, "get", arg)["arg"]

    def connect(self, address: str) -> None:
        '''Connect to device'''
        assert isinstance(address, str)
        with self.lock:
            asyncio.run_coroutine_threadsafe(self.__async__disconnect(), self.loop).result()
            asyncio.run_coroutine_threadsafe(self.__async__connect(address), self.loop).result()

    def disconnect(self) -> None:
        '''Disconnect from device'''
        with self.lock:
            asyncio.run_coroutine_threadsafe(self.__async__disconnect(), self.loop).result()

    def get_status(self) -> StatusData:
        '''Gets status data structure from device'''
        array = base64.b64decode(self.__get("status"))
        assert len(array) == 925
        data = StatusData.from_reader(_Reader(array))
        #assert data.abiVersion == 3
        return data

    def get_status_bits(self) -> StatusBits:
        '''Gets status bits of status data structure from device'''
        return self.get_status().statusBits

    def get_dial_done(self) -> bool:
        '''Gets whether dial of wavelength is done'''
        return bool(self.__get("dial_done"))

    def get_info(self) -> Info:
        '''Gets information data structure from device'''
        info = self.__get("info")
        return Info(
            info["name"],
            info["version"],
            info["revision"],
            info["serialNumber"],
            info["mac"],
        )

    def set_reboot(self)  -> None:
        '''Reboots the device'''
        try:
            return self.__set("reboot")
        # reboot will close the connection -> silently catch exception
        except websockets.exceptions.ConnectionClosedError:
            pass

    def set_shutter(self, channel: ShutterChannel, open_: bool) -> None:
        '''Sets a shutter open or closed'''
        assert isinstance(channel, ShutterChannel)
        assert isinstance(open_, bool)
        self.__set("shutter", channel.value, open_)

    def set_lambda(self,
                   wavelength: float,
                   request_shg: bool,
                   use_wlm_for_shg: bool = False) -> None:
        '''Sets a new wavelength (OPO) to dial'''
        self.__set("lambda", None, {
            "wavelength": wavelength,
            "requestShg": request_shg,
            "useWlmForShg": use_wlm_for_shg
        })

    def get_lambda(self):
        '''Gets the currently used parameters to dial a wavelength'''
        return self.__get("lambda")

    def set_lyot_inselective(self) -> None:
        '''Sets lyot to inselective position'''
        self.__set("lyot_inselective")

    def get_lyot_inselective(self) -> bool:
        '''Gets whether the lyot is in inselective position'''
        return bool(self.__get("lyot_inselective"))

    def set_lyot_target(self, target: int) -> None:
        '''Sets target position of lyot'''
        assert isinstance(target, int)
        self.__set("lyot_target", None, target)

    def get_lyot_target(self) -> int:
        '''Gets target position of lyot'''
        return int(self.__get("lyot_target"))

    def get_lyot_position(self) -> int:
        '''Gets current position of lyot'''
        return int(self.__get("lyot_position"))

    def set_piezo_mode(self, channel: PiezoChannel, mode: PiezoMode) -> None:
        '''Sets piezo mode'''
        assert isinstance(channel, PiezoChannel)
        assert isinstance(mode, PiezoMode)
        self.__set("piezo_mode", channel.value, mode.value)

    def get_piezo_mode(self, channel: PiezoChannel) -> PiezoMode:
        '''Gets piezo mode'''
        assert isinstance(channel, PiezoChannel)
        return PiezoMode(self.__get("piezo_mode", channel.value))

    def set_piezo_control_setpoint(self,
                                   channel: PiezoChannel,
                                   level: float) -> None:
        '''Sets piezo setpoint in control mode'''
        assert isinstance(channel, PiezoChannel)
        assert isinstance(level, (float, int))
        self.__set("piezo_control_setpoint", channel.value, level)

    def get_piezo_control_setpoint(self, channel: PiezoChannel) -> PiezoControlSource:
        '''Gets piezo setpoint in control mode'''
        assert isinstance(channel, PiezoChannel)
        return float(self.__get("piezo_control_setpoint", channel.value))

    def set_piezo_control_output_step(self,
                                      channel: PiezoChannel,
                                      step: float) -> None:
        '''Sets piezo output step in control mode'''
        assert isinstance(channel, PiezoChannel)
        assert isinstance(step, (float, int))
        self.__set("piezo_control_output_step", channel.value, step)

    def set_piezo_control_input_source(self,
                                       channel: PiezoChannel,
                                       source: PiezoControlSource) -> None:
        '''Sets piezo input source in control mode'''
        assert isinstance(channel, PiezoChannel)
        assert isinstance(source, PiezoControlSource)
        self.__set("piezo_control_input_source", channel.value, source.value)

    def get_piezo_control_input_source(self, channel: PiezoChannel) -> PiezoControlSource:
        '''Gets piezo input source in control mode'''
        assert isinstance(channel, PiezoChannel)
        return PiezoControlSource(self.__get("piezo_control_input_source", channel.value))

    def set_piezo_control_criterion_source(self,
                                           channel: PiezoChannel,
                                           source: PiezoControlSource) -> None:
        '''Sets piezo criterion source in control mode'''
        assert isinstance(channel, PiezoChannel)
        assert isinstance(source, PiezoControlSource)
        self.__set("piezo_control_criterion_source", channel.value, source.value)

    def get_piezo_control_criterion_source(self, channel: PiezoChannel) -> PiezoControlSource:
        '''Gets piezo criterion source in control mode'''
        assert isinstance(channel, PiezoChannel)
        return PiezoControlSource(self.__get("piezo_control_criterion_source", channel.value))

    def set_piezo_control_threshold(self,
                                    channel: PiezoChannel,
                                    level: float) -> None:
        '''Sets piezo threshold in control mode'''
        assert isinstance(channel, PiezoChannel)
        assert isinstance(level, (float, int))
        self.__set("piezo_control_threshold", channel.value, level)

    def get_piezo_control_threshold(self, channel: PiezoChannel) -> PiezoControlSource:
        '''Gets piezo threshold in control mode'''
        assert isinstance(channel, PiezoChannel)
        return float(self.__get("piezo_control_threshold", channel.value))

    def set_piezo_scan_settings(self, channel: PiezoChannel, settings: PiezoScanSettings) -> None:
        '''Sets piezo setting in scan mode'''
        assert isinstance(channel, PiezoChannel)
        assert isinstance(settings, PiezoScanSettings)
        self.__set("piezo_scan_settings", channel.value, {
            "min": settings.min,
            "max": settings.max,
            "rate": settings.rate
        })

    def get_piezo_scan_settings(self, channel: PiezoChannel) -> PiezoScanSettings:
        '''Gets piezo setting in scan mode'''
        assert isinstance(channel, PiezoChannel)
        settings = self.__get("piezo_scan_settings", channel.value)
        return PiezoScanSettings(
            min=settings['min'],
            max=settings['max'],
            rate=settings['rate'],
        )

    def set_piezo_manual_output(self, channel: PiezoChannel, value: float) -> None:
        '''Sets the output level of a piezo when in "manual" mode'''
        assert isinstance(channel, PiezoChannel)
        assert isinstance(value, (float, int))
        assert 0 <= value <= 100
        self.__set("piezo_manual_output", channel.value, value)

    def get_piezo_manual_output(self, channel: PiezoChannel) -> float:
        '''Gets the output level of a piezo when in "manual" mode'''
        assert isinstance(channel, PiezoChannel)
        return float(self.__get("piezo_manual_output", channel.value))

    def set_stepper_inactive_position(self, channel: StepperChannel) -> None:
        '''Sets stepper to go to inactive position'''
        assert isinstance(channel, StepperChannel)
        self.__set("stepper_inactive_position", channel.value)

    def set_stepper_period(self, channel: StepperChannel, period: int) -> None:
        '''Sets stepper target position by crystal period'''
        assert isinstance(channel, StepperChannel)
        assert isinstance(period, int)
        self.__set("stepper_period", channel.value, period)

    def get_stepper_period(self, channel: StepperChannel) -> int:
        '''Gets stepper target position mapped to crystal period (-1 if invalid)'''
        assert isinstance(channel, StepperChannel)
        return int(self.__get("stepper_period", channel.value))

    def set_stepper_target(self, channel: StepperChannel, position: int) -> None:
        '''Sets stepper target position'''
        assert isinstance(channel, StepperChannel)
        assert isinstance(position, int)
        self.__set("stepper_target", channel.value, position)

    def get_stepper_target(self, channel: StepperChannel) -> int:
        '''Gets stepper target position'''
        assert isinstance(channel, StepperChannel)
        return int(self.__get("stepper_target", channel.value))

    def get_stepper_position(self, channel: StepperChannel) -> int:
        '''Gets current position of stepper'''
        assert isinstance(channel, StepperChannel)
        return int(self.__get("stepper_position", channel.value))

    def set_stepper_start_homing(self, channel: StepperChannel) -> None:
        '''Starts a new homing of a stepper'''
        assert isinstance(channel, StepperChannel)
        self.__set("stepper_starthoming", channel.value)

    def set_tec_enabled(self, channel: TecChannel, enabled: bool) -> None:
        '''Sets TEC enabled or disabled'''
        assert isinstance(channel, TecChannel)
        assert isinstance(enabled, bool)
        self.__set("tec_enabled", channel.value, enabled)

    def get_tec_enabled(self, channel: TecChannel) -> bool:
        '''Gets whether TEC is enabled'''
        assert isinstance(channel, TecChannel)
        return bool(self.__get("tec_enabled", channel.value))

    def set_tec_setpoint(self, channel: TecChannel, temperature: float) -> None:
        '''Sets TEC temperature setpoints'''
        assert isinstance(channel, TecChannel)
        assert isinstance(temperature, (int, float))
        self.__set("tec_setpoint", channel.value, temperature)

    def get_tec_setpoint(self, channel: TecChannel) -> float:
        '''Gets TEC temperature setpoints'''
        assert isinstance(channel, TecChannel)
        return float(self.__get("tec_setpoint", channel.value))

    def set_wlm_enabled(self, enabled: bool) -> None:
        '''Sets whether control loop is enabled in AbsoluteLambda operation'''
        assert isinstance(enabled, bool)
        self.__set("wlm_enabled", None, enabled)

    def get_wlm_enabled(self) -> bool:
        '''Gets whether control loop is enabled in AbsoluteLambda operation'''
        return bool(self.__get("wlm_enabled", None))

    def set_wlm_setpoint(self, wavelength: float) -> None:
        '''Sets wavelength setpoint used in AbsoluteLambda operation'''
        assert isinstance(wavelength, (float, int))
        self.__set("wlm_setpoint", None, wavelength)

    def get_wlm_setpoint(self) -> float:
        '''Gets wavelength setpoint used in AbsoluteLambda operation'''
        return float(self.__get("wlm_setpoint", None))

    def set_wlm_kp(self, p_factor: float) -> None:
        '''Sets control loop P factor used in AbsoluteLambda operation'''
        assert isinstance(p_factor, (float, int))
        self.__set("wlm_kp", None, p_factor)

    def get_wlm_kp(self) -> float:
        '''Sets control loop P factor used in AbsoluteLambda operation'''
        return float(self.__get("wlm_kp", None))

    def set_wlm_ki(self, i_factor: float) -> None:
        '''Sets control loop I factor used in AbsoluteLambda operation'''
        assert isinstance(i_factor, (float, int))
        self.__set("wlm_ki", None, i_factor)

    def get_wlm_ki(self) -> float:
        '''Sets control loop I factor used in AbsoluteLambda operation'''
        return float(self.__get("wlm_ki", None))

    def get_mapping_field(self, channel: MappingFieldChannel):
        '''Gets mapping data of a field (crystal/lyot)'''
        assert isinstance(channel, MappingFieldChannel)
        return self.__get("mapping_field", channel.value)

    def set_etalon_optimize(self, scan_range: float = None) -> None:
        '''Starts etlalon optimization'''
        assert isinstance(scan_range, (int, float)) or scan_range is None
        self.__set("etalon_optimize", None, scan_range)

    def set_temperature_optimize(self,
                                 channel: TemperatureOptimizeChannel,
                                 start_temperature: float = None,
                                 steps: typing.List[ScanStep] = None) -> None:
        '''Starts temperature optimization'''
        assert isinstance(channel, TemperatureOptimizeChannel)
        if start_temperature is None:
            assert steps is None
            self.__set("temperature_optimize", channel.value, None)
        else:
            self.__set("temperature_optimize", channel.value, {
                "startTemperature": start_temperature,
                "steps": steps,
            })

    def set_lyot_scan(self, start_position: int, end_position: int) -> None:
        '''Starts lyot scan'''
        assert isinstance(start_position, int)
        assert isinstance(end_position, int)
        self.__set("lyot_scan", None, {
            "startPosition": start_position,
            "endPosition": end_position
        })

    def get_scan(self, channel: ScanChannel) -> list:
        '''Downloads latest scan data'''
        assert isinstance(channel, ScanChannel)
        return self.__get("scan", channel.value)

    def set_calibrate_reference(self) -> None:
        '''Starts OPO reference calibration'''
        self.__set("calibrate_reference")

    def set_stabilize_wlm(self, enabled: bool) -> None:
        '''Enters or Exits WLM Stabilization (AbsoluteLambda)'''
        assert isinstance(enabled, bool)
        self.__set("stabilize_wlm", None, enabled)

    def set_idle(self) -> None:
        '''Sets both statemachines into idle for full manual control'''
        self.__set("idle")
