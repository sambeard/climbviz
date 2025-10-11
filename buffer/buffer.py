from collections import defaultdict
import time

class SensorBuffer:
    feature_names = ["time", "x", "y", "z", "mag", "phi", "theta"]
    def __init__(self):
        self.data = defaultdict(lambda: {
            **{f:[] for f in self.feature_names}
        })


    def avg_n_samples(self):
        return sum([len(v) for v in self.data.values()]) / len(self.data.keys())
    	    
    def get_features_with_times(self, device_id, *features):
        if device_id not in self.data:
            return None
        data = self.data[device_id] 
        if features is None or type(features) is not tuple or len(features) == 0:
            features = self.feature_names
        
        times = data["time"]
        feature_data = {f: data[f] for f in features if f in data}

        # limit based on n samples
        shortest = min(min([len(v) for v in feature_data.values()]), len(times))
        times = times[-shortest:]
        for k, v in feature_data.items():
            feature_data[k] = v[-shortest:]

        if len(feature_data) == 1:
            feature_data = list(feature_data.values())[0]
        return times, feature_data
    

    def get_values(self, device_id, feature):
        if device_id not in self.data or feature not in self.data[device_id]:
            return None
        return self.data[device_id][feature]
    
    def get_keys(self, device_id, feature):
        if device_id not in self.data or feature not in self.data[device_id]:
            return None
        return self.data[device_id][feature]


    def update(self, device_id, _time, feature_data):
        self.data[device_id]['time'].append(_time)
        for k, v in feature_data.items():
            f = self.data[device_id][k]
            if k == "time":
                continue
            else:
                f.append(v)

