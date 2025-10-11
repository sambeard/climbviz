from interaction.base_interaction import BaseInteraction, IsHoldingInteraction, default_weighting_config
from interaction.base_renderer import Color
from interaction.ring_band_renderer import RingBandRenderer
import time

class PhiBandInteraction(BaseInteraction):
    @classmethod
    def default_config(cls):
        return {**default_weighting_config(),  

            "color": {"value": Color(0, 45, 100), "type": "Color"},
        }

    def __init__(self, name, device_mgr, buffer, mqtt, state_mgr):
        super().__init__(name, device_mgr, buffer, mqtt, state_mgr)
        self._init_renderer()

    def _init_renderer(self):
        self.renderer = RingBandRenderer(self.device_mgr, self.config["color"]["value"])

    def on_config(self, key, value):
        if key == "color":
            self._init_renderer()

    def update(self):
        now = time.time()
        window = self.config["window_s"]["value"]
        min_t = self.config["min_threshold"]["value"]
        max_t = self.config["max_threshold"]["value"]

        for dev in self.device_mgr.get_selected_devices():
            mag_vals = self.buffer.get_recent(dev, "mag", window)
            phi_vals = self.buffer.get_recent(dev, "phi", 0.05)

            if not mag_vals or not phi_vals:
                continue

            avg_mag = sum(mag_vals) / len(mag_vals)
            if avg_mag < min_t:
                self.device_mgr.send_led_data(dev, [0, 0, 0] * 25)
                continue

            center = phi_vals[-1]
            width = min(1.0, max(0.0, (avg_mag - min_t) / (max_t - min_t)))
            self.renderer.render(dev, center, width)
