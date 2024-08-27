from nspyre import InstrumentManager

class MyInstrumentManager(InstrumentManager):
    def __init__(self):
        super().__init__(register_gateway=False)
        self.register_gateway(port=42068)  # primary inserv 
        self.register_gateway(port=42067)  # secondary inserv;  ***SSH tunnel should already exist*** to Awsch@192.168.1.95 port 42057
