from nspyre import StreamingList, DataSink
from nspyre.data import save


with DataSink('eomScan') as sink:
    sink.pop()
    save.save_json('eomScan_0-2Vaom_5000Hz.json',sink.data)
        