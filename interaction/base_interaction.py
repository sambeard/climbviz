from interaction.base_renderer import BaseRenderer, Color
from interaction.gradient_renderer import GradientRenderer
from interaction.solid_renderer import SolidColorRenderer
import time

class BaseInteraction:
    def __init__(self, name, device_mgr, buffer, mqtt, state_mgr):
        self.name = name
        self.device_mgr = device_mgr
        self.buffer = buffer
        self.mqtt = mqtt
        self.state_mgr = state_mgr

        self.config = self.default_config()
        self.register_config()

    @classmethod
    def default_config(cls):
        return {}

    def clear(self):
        for dev in self.device_mgr.get_all_devices():
            self.device_mgr.send_led_data(dev, BaseRenderer.to_bytes([Color(0,0,0)]* 25))

    def on_select(self):
        self.clear()

    def register_config(self):
        for key, meta in self.config.items():
            self.state_mgr.register_param("interaction", self.name, key, meta["value"], meta["type"])

    def update_config(self, new_config: dict):
        for key, value in new_config.items():
            if key in self.config:
                self.config[key]["value"] = value
                self.on_config(key, value)

    def on_config(self, key: str, value):
        """Called when a config value is updated. Override as needed."""
        pass

    def get_feature(self, dev, name):
        return self.buffer.get_values(dev, name)

    def get_config(self, key):
        return self.config[key]["value"]

    def update(self):
        raise NotImplementedError("Define logic in subclass.")


# ========== OffInteraction ==========
class OffInteraction(BaseInteraction):
    def __init__(self, name, device_mgr, buffer, mqtt, state_mgr):
        super().__init__(name, device_mgr, buffer, mqtt, state_mgr)
        self.renderer = SolidColorRenderer(device_mgr, Color(0, 0, 0))

    def update(self):
        pass

    def on_config(self, key: str, value):
        for dev in self.device_mgr.get_all_devices():
            self.renderer.render(dev)

# ========== DebugOnInteraction ==========
class DebugInteraction(BaseInteraction):
    @classmethod
    def default_config(cls):
        return {
            "color": {"value": Color(20, 20, 20), "type": "Color", "label": "Debug Color"}
        }

    def __init__(self, name, device_mgr, buffer, mqtt, state_mgr):
        super().__init__(name, device_mgr, buffer, mqtt, state_mgr)
        self.on_renderer = SolidColorRenderer(device_mgr, self.config["color"]["value"])
        self.off_renderer = SolidColorRenderer(device_mgr, Color(0, 0, 0))

    def on_config(self, key, value):
        if key == "color":
            self.on_renderer = SolidColorRenderer(self.device_mgr, value)

    def update(self):
        for dev in self.device_mgr.get_all_devices():
            if dev in self.device_mgr.selected:
                self.on_renderer.render(dev)
            else:
                self.off_renderer.render(dev)

def default_weighting_config(min_t=2.5, max_t=35, window_s=.5):
    return {
        "min_threshold": {"value": 2.5, "type": "float"},
        "max_threshold": {"value": 35.0, "type": "float"},
        "window_s": {"value": 0.5, "type": "float"}
    }

# ========== DebugHoldingInteraction ==========
class IsHoldingInteraction(BaseInteraction):
    @classmethod
    def default_config(cls):
        return {
            "color_low": {"value": Color(0, 0, 0), "type": "Color"},
            "color_start": {"value": Color(2, 15, 0), "type": "Color"},
            "color_end": {"value": Color(150, 0, 0), "type": "Color"},
            **default_weighting_config()
        }

    def __init__(self, name, device_mgr, buffer, mqtt, state_mgr):
        super().__init__(name, device_mgr, buffer, mqtt, state_mgr)
        self._init_renderers()

    def _init_renderers(self):
        self.not_weighted_renderer = SolidColorRenderer(self.device_mgr, self.config["color_low"]["value"])
        self.weighted_renderer = GradientRenderer(
            self.device_mgr,
            self.config["color_start"]["value"],
            self.config["color_end"]["value"]
        )

    def on_config(self, key, value):
        if key in ["color_low", "color_start", "color_end"]:
            self._init_renderers()

    def update(self):
        now = time.time()

        
        window = self.get_config("window_s")
        min_t = self.get_config("min_threshold")
        max_t = self.get_config("max_threshold")

        for dev in self.device_mgr.get_selected_devices():
            mags = self.buffer.get_recent(dev, 'mag', window)
            if not mags:
                continue
            avg = sum(mags) / len(mags)
            if avg < min_t:
                self.not_weighted_renderer.render(dev)
            else:
                t = min(1.0, max(0.0, (avg - min_t) / (max_t - min_t)))
                self.weighted_renderer.render(dev, t)