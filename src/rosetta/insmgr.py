from nspyre import InstrumentManager

class MyInstrumentManager(InstrumentManager):
    def __init__(self):
        super().__init__(register_gateway=False)
        self.register_gateway()  # primary inserv ("local")
        #self.register_gateway("192.168.1.95")  # secondary inserv ("remote");  c-wave
