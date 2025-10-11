
import time
import threading

from buffer.recordingbuffer import RecordingBuffer
from interaction.base_analysis import MaxMag, TotalMag, TimeOnHold
from interaction.phi_analysis import PhiAnalysis

class AnalysisEngine:
    def __init__(self, config, device_manager, mqtt_manager, state_manager, fps = 15):
        self.config = config
        self.device_mgr = device_manager
        self.mqtt = mqtt_manager
        self.state = state_manager
        self.buffer = None
        self.FPS = fps

        self.analyses = {
            "MaxMag": MaxMag("MaxMag", self.device_mgr, self.mqtt, self.state),
            "TotalMag": TotalMag("TotalMag", self.device_mgr, self.mqtt, self.state),
            "TimeOnHold": TimeOnHold("TimeOnHold", self.device_mgr, self.mqtt, self.state),
            "PhiAnalysis": PhiAnalysis("PhiAnalysis", self.device_mgr, self.mqtt, self.state),
        }

        self.default_analysis = "MaxMag"
        if not self.state.get("analysis/active"):
            self.state.set("analysis/active", self.default_analysis)

        self.set_analysis(self.state.get("analysis/active", self.default_analysis))

        self.active = False

    def get_analysis(self):
        analysis_name = self.state.get("analysis/active", "MaxMag")
        return self.analyses[analysis_name]

    def set_analysis(self, analysis_name):
        if analysis_name not in self.analyses:
            return

        self.state.set("analysis/active", analysis_name)
        analysis = self.get_analysis()
        param_path = f"analysis/params/{analysis_name}"
        config = self.state.get(param_path, {})

        clean_config = {
            k: v["value"]
            for k, v in config.items()
            if isinstance(v, dict) and "value" in v
        }
        analysis.update_config(clean_config)
        analysis.on_select()

    def init_playback_buffer(self):
        file_name = self.state.get("analysis/playback_buffer", None)
        if file_name:
            self.buffer = RecordingBuffer.load_from_csv(file_name)
            self.state.set("analysis/playback_buffer", file_name)
        else:
            self.buffer = None

    def set_playback_buffer_name(self, file_name):
        self.state.set("analysis/playback_buffer", file_name)
        self.init_playback_buffer()

    def get_playback_buffer_name(self):
        return self.state.get("analysis/playback_buffer", None)

    def render(self):
        analysis = self.get_analysis()
        for dev in self.device_mgr.get_all_devices():

            self.device_mgr.send_led_data(dev,[0,0,0]*25)
        if analysis:
            analysis.set_recording_buffer(self.buffer)
            analysis.calculate()
