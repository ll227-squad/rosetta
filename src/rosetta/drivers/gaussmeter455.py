"""
Lakeshore Gaussmeter455 Driver

Progamming manual: 
https://www.lakeshore.com/docs/default-source/product-downloads/455_manual.pdf?sfvrsn=244bc81_1

"""
import logging
import pyvisa

logger = logging.getLogger(__name__)

class Gaussmeter455Instrument:
    def __init__(self, address):
        """
        Args:
            address: PyVisa resource path.
        """
        self.address = address
        self.rm = pyvisa.ResourceManager()

    def open(self):
        try:
            self.device = self.rm.open_resource(self.address)
        except Exception as err:
            raise ConnectionError(f'Failed connecting to 455Gaussmeter @ [{self.address}]') from err
        # 1 second timeout
        self.device.timeout = 1000
        self.idn = self.device.query('*IDN?').strip()
        logger.info(f'Connected to 455Gaussmeter[{self}]')
        return self

    def close(self):
        self.device.close()

    def __str__(self):
        return f'{self.address} {self.idn}'

    def __enter__(self):
        self.open()
        return self
    
    def __exit__(self, *args):
        self.close()    

    def clear_interface(self):
        """
        Clears the bits in the Standard Event Status Register 
        and Operation Event Register and terminates all
        pending operations. Clears the interface, but not the instrument. 
        The related instrument command is *RST.

        The Operation Event Register reports the following interface related 
        instrument events: ramp done, datalog done, alarm,
        new reading, field overload, no probe.
        """
        self.device.write('*CLS')

    def enable_register(self, bit_weighting):
        """
        This command programs the enable register using
        a decimal value which corresponds to the binary-weighted 
        sum of all bits in the register
        """
        self.device.write(f'*ESE {bit_weighting}')

    def read_event_register(self):
        """
        Reads the SESR
        """
        return self.device.query('*ESE?').strip()

    def read_and_clear_event_register(self):
        """
        Reads and clears the SESR
        """
        return self.device.query('*ESR?').strip()
    
    def id(self):
        """
        Returns identiifcation i.e manufactureer, model, 
        serial number, fimware revision date
        """
        return self.device.query('*IDN?').strip()
    
    def opc(self):
        """
        Operation complete commannd 
        """
        self.device.write('*OPC')
    
    def opc_query(self):
        return self.device.query('*OPC?').strip()

    def reset(self):
        self.device.write('*RST')

    def service_request(self):
        self.device.write('*SRE')

    def service_request_query(self):
        return self.device.query('*SRE?').strip()
    
    def check_status_byte(self):
        return self.device.query('*STB?').strip()
    
    def self_test(self):
        return self.device.query('*TST?').strip()
    
    def set_alarm(self, switch, mode, low_value, high_value, out_or_in):
        self.device.write(f'ALARM {switch}, {mode}, {low_value}, {high_value}, {out_or_in}')

    def check_alarm_param(self):
        return self.device.query('ALARM?').strip()

    def check_alarm_status(self):
        return self.device.query('ALARMST?').strip()
    
    def set_analog_output(self, mode, polarity, low_value, high_value, manual_value, voltage_limit):
        self.device.write(f'ANALOG {mode}, {polarity}, {low_value}, {high_value}, {manual_value}, {voltage_limit}')
    
    def check_analog_param(self):
        return self.device.query('ANALOG?').strip()
    
    def check_percentage_of_analog(self):
        return self.device.query('AOUT?').strip()
    
    def set_auto_range(self, switch):
        self.device.write(f'AUTO {switch}')

    def check_auto_range(self):
        return self.device.query('AUTO?').strip()
    
    def set_baud_rate(self, rate):
        self.device.write(f'BAUD {rate}')

    def check_baud_rate(self):
        return self.device.query('BAUD?').strip()
    
    def set_alarm_beeper(self):
        self.device.write('BEEP')

    def check_beeper_state(self):
        return self.device.query('BEEP?').strip()
    
    def set_brightness(self, state):
        self.device.write(f'BRIGT {state}')
    
    def check_brightness(self):
        return self.device.query('BRIGT?').strip()
    
    def set_to_default(self):
        self.device.write('DFLT 99')

    def set_display(self, item):
        self.device.write(f'DISPLAY {item}')

    def check_display(self):
        return self.device.quesry('DISPLAY?')

    def set_IEEE_commands(self, terminator, EOI_enable, address):
        self.device.write(f'IEEE {terminator}, {EOI_enable}, {address}')

    def check_IEEE_commands(self):
        return self.device.query('IEEE?').strip()

    def check_last_key(self):
        return self.device.query('KEYST?').strip()

    def set_front_panel_lock(self, state, code):
        self.device.write(f'LOCK {state}, {code}')

    def check_front_panel_lock(self):
        return self.device.query('LOCK?').strip()
    
    def set_maxhold(self, switch, mode, display):
        self.device.write(f'MXHOLD {switch}, {mode}, {display}')

    def check_maxhold(self):
        return self.device.query('MODE?').strip()
    
    def reset_maxhold(self):
        self.device.write('MXRST')
    
    def set_interface_mode(self, mode):
        self.device.write(f'MODE {mode}')

    def check_interface_mode(self):
        return self.device.query('MODE?').strip() ###has the same character input as check maxhold

    def check_operational_status(self):
        return self.device.query('OPST?').strip()
    
    def set_operational_status_enable(self):
        self.device.write('OPSTE')

    def check_operational_status_enable(self):
        return self.device.query('OPSTE?').strip()
    
    def check_operational_status_registry(self):
        return self.device.query('OPSTR?').strip()
    
    def set_peak_readings(self):
        self.device.write('PKRST')

    def set_probe_field(self, switch):
        self.device.write(f'PRBFCOMP {switch}')

    def check_probe_field(self):
        return self.device.query('PRBFCOMP?').strip()

    def check_probe_sensitivity(self):
        """
        Returns value in mV/kG
        """
        return self.device.query('PRBSENS?').strip()
    
    def check_probe_serial_number(self):
        return self.device.query('PRBSNUM?').strip()
    
    def set_probe_temp_state(self, switch):
        self.device.write(f'PRBTCOMP {switch}')
    
    def check_probe_temp_state(self):
        return self.device.query('PRBTCOMP?').strip()
    
    def set_field_range(self, range):
        self.device.write(f'RANGE {range}').strip()

    def check_field_range(self):
        return self.device.query('RANGE?').strip()

    def check_field_reading(self):
        return self.device.query('RDGFIELD?').strip()

    def set_measurement_mode(self, mode, dc_resolution, rms_mode, peak_mode, peak_disp):
        self.device.write(f'RDGMODE {mode}, {dc_resolution}, {rms_mode}, {peak_mode}, {peak_disp}')

    def check_measurement_mode(self):
        return self.device.query('RDGMODE?').strip()

    def check_frequnecy_reading(self):
        return self.device.query('RDGFRQ?').strip()

    def check_max_and_min_reading(self):
        return self.device.query('RDGMNMX?').strip()

    def check_resistance_reading(self):
        return self.device.query('RDGOHM?').strip()

    def check_peak_reading(self):
        return self.device.query('RDGPEAK?').strip()
    
    def check_relative_field_reading(self):
        return self.device.query('RDGREL?').strip()
    
    def check_probe_temp_reading(self):
        return self.device.query('RDGTEMP?').strip()
    
    def set_relative_mode(self, state = "0", setpoint_source = "2"):  ###Start here
        """
        Lets user see small variations on larger fields. When mode is on, user' will see
        readings on the display. Reaadings will have a small delta sigh to signify display
        Dispalyed reading = presnt field - relative setpoint

        State -- if mode should be on/off
        '0' = Off
        '1' = On

        Set_point-- how setpoitn shoudl be configured, by user or by present field
        '1' = User Defined
        '2' = Presetnt field 
        """
        self.device.write(f'REL {state} {setpoint_source}')

    def check_state_of_relative_mode(self):
        """
        Returns state of mode 
        """
        response = self.device.query('REL?').strip()
        options = {"0":"Off", "1":"On"}
        options = {"1":"Celcius", "2":"Kelvin"}
        for key in options:
            if key == response:
                return options[response]

    def set_relay_param(self, relay_num, mode, alarm_type):
        """
        Configures the following parameters
        Relay_num -- Relay to use
        1 = Relay 1
        2 = Relay 2

        mode
        0 = Off
        1 = On
        2 = Alarm 

        alarm_type
        1 = Low Alarm
        2 = High Alarm
        """
        self.device.write(f'RELAY {relay_num}, {mode}, {alarm_type}')

    def check_relay_param(self, relay_num):
        """
        Retunrns the parameters for a giiven relay
        Relay_num -- Relay to check
        1 = Relay 1
        2 = Relay 2
        """
        list = self.device.query(f'RELAY? {relay_num}').strip().split(",")
        response1 = list[0]
        response2= list[1]
        print(response1, response2)
        options1 = {"0":"Off", "1":"On"}
        for key in options1:
            if key == response1:
                mode = options1[response1]
        options2  = {"2":"High Alarm", "1":"Low Alarm"}
        for key in options2:
            if key == response2:
                alarm = options2[response2]
        statement = "State:{m}, Alarm type:{a}"
        return statement.format(m = mode, a = alarm)
    
    def check_relay_status(self, relay_num):
        """
        Specifify which relay you are checking.
        Return relay is on/off
        """
        response = self.device.query(f'RELAYST? {relay_num}').strip()
        options = {"0":"Off", "1":"On"}
        for key in options:
            if key == response:
                return options[response]
    
    def set_relative_setpoint(self, setpoint):
        """
        Specifies the setpoint to use in the relative calculation: +/- 350 kG
        Configure the relative setpoint as 1200 Gauss(if units in Gauss). The relative 
        reading will use this value if relative is using the user defined setpoint. 
        Refer to set_relalative_mode fucntion
        """
        self.device.write(f'RELSP {setpoint}')

    def check_relative_setpoint(self):
        "Reuturns relative setpoint"
        return self.device.query('RELSP?').strip()
    
    def set_probe_temp_unit(self, units):
        """
        Sets tempurature unit to Celcius or Kelvin 
        "1" = Celcius
        "2" = Kelvin 
        """
        self.device.write(f'TUNIT {units}')

    def check_probe_temp_unit(self):
        """
        Returns temp setting 
        """
        response = self.device.query('TUNIT?').strip()
        options = {"1":"Celcius", "2":"Kelvin"}
        for key in options:
            if key == response:
                return options[response]
    
    def check_probe_type(self):
        """
        Returns probe type
        """
        response = self.device.query('TYPE?').strip()
        options = {"40": "high sensitivity", "41": "high stability", "42": "Ultra high sensitivity", 
                   "50": " user programmable cable/high sensitivity probe", "51": "user programmable cable/high stability probe",
                   "52": " user programmable cable/ultra-high sensitivity probe"}
        for key in options:
            if key == response:
                return options[response]

    
    def set_field_units(self, units = '2'):
        """
        Sets units. Default will set to Tesla 
        '1' = Guass
        '2' = Tesla
        '3' = Oersted
        '4' = Amp/meter
        """
        self.device.write(f'UNIT {units}')

    def check_field_units(self):
        """
        Returns unit of instrument of measuremnt
        """
        response = self.device.query('UNIT?').strip()
        options = {'1': "Guass", '2':"Tesla", '3':"Oersted", '4':"Amp/meter"}
        for key in options:
            if key == response:
                return options[response]

    def clear_zprobe(self):
        """
        Resets the value stored from the ZPROBE command.
        """
        self.device.write('ZCLEAR')

    def initiate_zprobe(self):
        """
        Initiates the Zero Probe function. Place the probe 
        in zero gauss chamber before issuing this command
        """
        self.device.write('ZPROBE')
    
