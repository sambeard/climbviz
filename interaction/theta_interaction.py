from interaction.base_interaction import BaseInteraction, IsHoldingInteraction, default_weighting_config
from interaction.base_renderer import Color
from interaction.gradient_renderer import GradientRenderer
import time

class ThetaInteraction(BaseInteraction):
    @classmethod
    def default_config(cls):
        return {**default_weighting_config(),  

            "colorPos": {"value": Color(0, 100, 0), "type": "Color"},
            "colorNeg": {"value": Color(100, 0, 0), "type": "Color"},
            "colorMid": {"value": Color(0, 0, 0), "type": "Color"},
        }

    def __init__(self, name, device_mgr, buffer, mqtt, state_mgr):
        super().__init__(name, device_mgr, buffer, mqtt, state_mgr)
        self._init_renderer()

    def _init_renderer(self):
        self.rendererPos = GradientRenderer(self.device_mgr, self.config["colorMid"]["value"], self.config["colorPos"]["value"])
        self.rendererNeg = GradientRenderer(self.device_mgr, self.config["colorMid"]["value"], self.config["colorNeg"]["value"])

    def on_config(self, key, value):
        if key == "color":
            self._init_renderer()

    def update(self):
        window = self.config["window_s"]["value"]
        min_t = self.config["min_threshold"]["value"]
        max_t = self.config["max_threshold"]["value"]

        for dev in self.device_mgr.get_selected_devices():
            mag_vals = self.buffer.get_recent(dev, "mag", window)
            theta_vals = self.buffer.get_recent(dev, "theta", 0.05)

            if not mag_vals or not theta_vals:
                continue

            avg_mag = sum(mag_vals) / len(mag_vals)
            if avg_mag < min_t:
                self.device_mgr.send_led_data(dev, [0, 0, 0] * 25)
                continue

            theta = theta_vals[-1]
            amount = min(1.0, .1+ avg_mag  / max_t)
            if (theta > 0):
                self.rendererPos.render(dev, theta, brightness=amount)
            else:
                self.rendererPos.render(dev, -theta, brightness=amount)
