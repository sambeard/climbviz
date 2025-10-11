from buffer.recordingbuffer import RecordingBuffer
from interaction.base_renderer import BaseRenderer, Color
from interaction.gradient_renderer import GradientRenderer
from interaction.solid_renderer import SolidColorRenderer
from interaction.base_interaction import default_weighting_config
import time

class BaseAnalysis:
    def __init__(self, name, device_mgr, mqtt, state_mgr):
        self.name = name
        self.device_mgr = device_mgr
        self.mqtt = mqtt
        self.state_mgr = state_mgr
        self.buffer= None

        self.config = self.default_config()
        self.register_config()

    @classmethod
    def default_config(cls):
        return {
            # Use this to define default config values
        }

    def set_recording_buffer(self, buffer: RecordingBuffer):
        self.buffer = buffer

    def on_select(self):
        self.calculate()

    def register_config(self):
        for key, meta in self.config.items():
            self.state_mgr.register_param("analysis", self.name, key, meta["value"], meta["type"])

    def update_config(self, new_config: dict):
        for key, value in new_config.items():
            if key in self.config:
                self.config[key]["value"] = value
                self.on_config(key, value)

    def on_config(self, key: str, value):
        """Called when a config value is updated. Override as needed."""
        pass

    def get_feature(self, dev, name):
        if self.buffer is None:
            return []
        return self.buffer.get_values(dev, name)

    def get_config(self, key):
        return self.config[key]["value"]

    def calculate(self):
        raise NotImplementedError("Define logic in subclass.")


class MaxMag(BaseAnalysis):

    def __init__(self, name, device_mgr, mqtt, state_mgr):
        super().__init__(name, device_mgr, mqtt, state_mgr)
        self._init_renderer()

    @classmethod
    def default_config(cls):
        return {
            **default_weighting_config(),
            "colorA": {"value": Color(10, 10, 10), "type": "Color"},
            "colorB": {"value": Color(0, 0, 100), "type": "Color"},
            "colorC": {"value": Color(180, 0, 125), "type": "Color"},
            "colorD": {"value": Color(225, 0, 0), "type": "Color"},

        }
    
    def on_config(self, key: str, value):
        """Called when a config value is updated. Override as needed."""
        super().on_config(key, value)
        if "color" in key:
            self.renderer = GradientRenderer(
                self.device_mgr,
                self.config["colorA"]["value"],
                self.config["colorB"]["value"],
                self.config["colorC"]["value"],
                self.config["colorD"]["value"],
            )

    def _init_renderer(self):
        self.renderer = GradientRenderer(
            self.device_mgr,
            self.config["colorA"]["value"],
            self.config["colorB"]["value"],
            self.config["colorC"]["value"],
            self.config["colorD"]["value"],
        )

    def calculate(self):
        min_t = self.get_config("min_threshold") if "min_threshold" in self.config else float('inf')
        max_t = self.get_config("max_threshold") if "max_threshold" in self.config else float('inf')
        for dev in self.device_mgr.get_selected_devices():
            mags = self.get_feature(dev, "mag")
            if not mags:
                self.renderer.render(dev, -1)
                continue
            weighted_mags = [mag for mag in mags if mag > min_t]
            if not weighted_mags:
                self.renderer.render(dev, -1)
                continue
            max_mag = max(weighted_mags) / max_t
            self.renderer.render(dev, max_mag)

class TotalMag(BaseAnalysis):

    def __init__(self, name, device_mgr, mqtt, state_mgr):
        super().__init__(name, device_mgr, mqtt, state_mgr)
        self._init_renderer()

    @classmethod
    def default_config(cls):
        return {
            **default_weighting_config(),
            "colorA": {"value": Color(10, 10, 10), "type": "Color"},
            "colorB": {"value": Color(0, 0, 100), "type": "Color"},
            "colorC": {"value": Color(180, 0, 125), "type": "Color"},
            "colorD": {"value": Color(225, 0, 0), "type": "Color"},

        }
    
    def on_config(self, key: str, value):
        """Called when a config value is updated. Override as needed."""
        super().on_config(key, value)
        if "color" in key:
            self.renderer = GradientRenderer(
                self.device_mgr,
                self.config["colorA"]["value"],
                self.config["colorB"]["value"],
                self.config["colorC"]["value"],
                self.config["colorD"]["value"],
            )

    def _init_renderer(self):
        self.renderer = GradientRenderer(
            self.device_mgr,
            self.config["colorA"]["value"],
            self.config["colorB"]["value"],
            self.config["colorC"]["value"],
            self.config["colorD"]["value"],
        )

    def calculate(self):
        min_t = self.get_config("min_threshold") if "min_threshold" in self.config else float('inf')
        max_t = self.get_config("max_threshold") if "max_threshold" in self.config else float('inf')
        for dev in self.device_mgr.get_selected_devices():
            mags = self.get_feature(dev, "mag")
            if not mags:
                self.renderer.render(dev, -1)
                continue
            mags_t = [mag for mag in mags  if mag > min_t]
            if not mags_t:
                self.renderer.render(dev, -1)
                continue
            total_mag = sum(mags_t) / len(mags_t) # devide by all samples
            cval = min(0, max(total_mag / max_t, 1))
            self.renderer.render(dev, cval)
            cval = total_mag / max_t

class TimeOnHold(BaseAnalysis):

    def __init__(self, name, device_mgr, mqtt, state_mgr):
        super().__init__(name, device_mgr, mqtt, state_mgr)
        self._init_renderer()

    @classmethod
    def default_config(cls):
        return {
            **default_weighting_config(min_t=4),
            "colorA": {"value": Color(10, 10, 10), "type": "Color"},
            "colorB": {"value": Color(0, 0, 100), "type": "Color"},
            "colorC": {"value": Color(180, 0, 125), "type": "Color"},
            "colorD": {"value": Color(225, 0, 0), "type": "Color"},

        }
    
    def on_config(self, key: str, value):
        """Called when a config value is updated. Override as needed."""
        super().on_config(key, value)
        if "color" in key:
            self.renderer = GradientRenderer(
                self.device_mgr,
                self.config["colorA"]["value"],
                self.config["colorB"]["value"],
                self.config["colorC"]["value"],
                self.config["colorD"]["value"],
            )

    def _init_renderer(self):
        self.renderer = GradientRenderer(
            self.device_mgr,
            self.config["colorA"]["value"],
            self.config["colorB"]["value"],
            self.config["colorC"]["value"],
            self.config["colorD"]["value"],
        )

    def calculate(self):
        min_t = self.get_config("min_threshold") if "min_threshold" in self.config else float('inf')
        max_t = self.get_config("max_threshold") if "max_threshold" in self.config else float('inf')
        for dev in self.device_mgr.get_selected_devices():
            mags = self.get_feature(dev, "mag")
            if not mags:
                self.renderer.render(dev, -1)
                continue
            mags_t = [mag for mag in mags  if mag > min_t]
            if not mags_t:
                self.renderer.render(dev, -1)
                continue
            duty_cycle = len(mags_t) / len(mags) # devide by all samples
            cval = duty_cycle
            self.renderer.render(dev, cval)