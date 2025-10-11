from core.mocking import MockDevice
import pandas as pd
import time

class PlaybackDevice(MockDevice):
    def __init__(self, device_id, mqtt_client, df):
        super().__init__(device_id, mqtt_client, None)
        self.df = df

    def _setup(self):
        self._wait_time = pd.Timedelta(seconds=self.df.index[0])
        print("Initial wait time:", self._wait_time)
        self._idx =0

    def load_file(self, file):
        df = pd.read_csv(file, index_col=[0,1], header= [0], parse_dates=["time"])

    def _handle_pause(self, paused):
        pass

    def _wait_till_next(self):
        print("hello", self._wait_time)
        time.sleep(self._wait_time.total_seconds())

    def _gen_payload(self, t):
        this, next = self.df.iloc[self._idx], self.df.iloc[self._idx+1]
        if next is None or next.index <= this.index:
            return None
        self._wait_time = next.index - this.index
        self._idx += 1
        return this.to_dict()

class PlaybackEngine:
    def __init__(self, mqtt_manager, state_manager):
        self.mqtt_manager = mqtt_manager
        self.state = state_manager
        self.devices = {}
        self.running = False

    def start(self):
        client = self.mqtt_manager.client
        if self.running:
            return
        self.running = True
        file = self.state.get("playback/file", "")

        df = self.read_df(file)
        device_ids = df.index.get_level_values("device_id").unique().to_list()

        for id in device_ids:
            _df = self.prepare_device_df(df, id)
            device = PlaybackDevice(id, client, _df)
            device.start()
            self.devices[id]= device

    def prepare_device_df(self, df, id):
        """ Extracts and normalizes the dataframe for a specific device ID. """
        start_time = df.index.get_level_values("time").min()
        _df = df.xs(id, level="device_id")
        _df.reset_index(["time"], inplace=True, drop=True)
        _df.index = _df.index - start_time
        return _df

    def read_df(self, file):
        df = pd.read_csv(file, index_col=[0,1], header= [0], parse_dates=["time"])
        return df

    def stop(self):
        if not self.running:
            return
        self.running = False
        for device in self.devices:
            device.stop()
        self.devices.clear()