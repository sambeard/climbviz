from interaction.base_interaction import BaseInteraction, default_weighting_config
from interaction.base_renderer import Color
from interaction.gradient_renderer import GradientRenderer
from interaction.ring_band_renderer import RingBandRenderer
import numpy as np
import math

class ResultantDirection(BaseInteraction):
    @classmethod
    def default_config(cls):
        return {
            **default_weighting_config(),
            "colorBand": {"value": Color(0, 180, 225), "type": "Color"},
        }

    def __init__(self, name, device_mgr, buffer, mqtt, state_mgr):
        super().__init__(name, device_mgr, buffer, mqtt, state_mgr)
        self._init_renderers()

    def _init_renderers(self):
        self.band = RingBandRenderer(
            self.device_mgr,
            self.config["colorBand"]["value"]
        )

    def on_config(self, key, value):
        if key in ["colorGradientStart", "colorGradientEnd", "colorBand"]:
            self._init_renderers()

    def update(self):
        # Fetch configuration parameters
        window = self.config["window_s"]["value"]
        min_t = self.config["min_threshold"]["value"]
        upper_limit = self.config["max_threshold"]["value"]

        # Collect recent sensor vectors and magnitudes for selected devices
        device_vecs = {}
        device_mags = {}

        for dev in self.device_mgr.get_selected_devices():
            x_vals = self.buffer.get_recent(dev, "x", window)
            y_vals = self.buffer.get_recent(dev, "y", window)
            mag_vals = self.buffer.get_recent(dev, "mag", window)

            if not x_vals or not y_vals or not mag_vals:
                continue

            fx = sum(x_vals) / len(x_vals)
            fy = sum(y_vals) / len(y_vals)
            mag = sum(mag_vals) / len(mag_vals)

            if mag <= min_t:
                self.device_mgr.send_led_data(dev, self.band.to_bytes([Color(0,0,0)]*25))
                continue
            device_vecs[dev] = np.array([fx, fy])
            device_mags[dev] = mag

        if not device_vecs:
            return

        # Compute the wall-wide resultant vector from all active devices
        total_force = sum(vec for dev, vec in device_vecs.items())
        norm = np.linalg.norm(total_force)
        if norm == 0:
            return
        resultant = total_force / norm
        phi = math.atan2(resultant[1], resultant[0]) / (2 * math.pi)
        phi = (phi + .75) % 1.0  # normalize to [0, 1]
        n_factor = min(max(0.0, norm / (upper_limit*2)), 1.0)


        for dev in device_vecs.keys():
            mag = device_mags[dev]
            bri = min(max(0.0, mag / (upper_limit)), 1.0)
            self.band.render(dev, center=phi, width=.25, brightness=bri)
