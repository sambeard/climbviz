
from collections import defaultdict, deque
import csv
import time
from buffer.buffer import SensorBuffer

class DeviceBuffer(SensorBuffer):
    def __init__(self, buffer_len=30):
        super().__init__()
        self.buffer_len = buffer_len

    def update(self, device_id, _time, feature_data):
        super().update(device_id, _time,feature_data)
        # remove old data
        _now = time.time()
        _dat = self.data[device_id]
        while _dat["time"] and (_now - _dat["time"][0] > self.buffer_len):
            for k in _dat.keys():
                _dat[k].pop(0)

    def get_recent(self, device_id, feature, window):
        _now = time.time()
        since_time = _now - window
        if device_id not in self.data or feature not in self.data[device_id]:
            return None
        
        times,values = self.get_features_with_times(device_id, feature)
        return [v for v, t in zip(values, times) if t >= since_time and t <= _now]



