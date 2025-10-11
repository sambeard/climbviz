from collections import defaultdict
import csv
import pandas as pd
from buffer.buffer import SensorBuffer

class RecordingBuffer(SensorBuffer):
    def __init__(self):
        super().__init__()

    @classmethod
    def load_from_csv(cls, path):
        instance = cls()
        with open(path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                dev = row["device_id"]
                time = row["time"]
                features = {k: float(v) for k, v in row.items() if k not in ["device_id", "time"]}
                instance.update(dev, float(time), features)
        return instance

    @property
    def devices(self):
        return list(self.data.keys())

    def export_csv(self, path):
        dfs = []
        # Organize by device, time -> feature dict
        for dev, content in self.data.items():
            _df = pd.DataFrame(content)
            _df["device_id"] = dev
            _df.set_index(["device_id", "time"], inplace=True)
            dfs.append(_df)          
        # Concatenate all dataframes
        df = pd.concat(dfs)
        # Sort by device_id and time
        df.sort_index(level=1,inplace=True)
        df.to_csv(path, index=True, header=True)

