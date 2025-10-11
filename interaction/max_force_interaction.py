from interaction.base_interaction import BaseInteraction, default_weighting_config
from interaction.base_renderer import Color
from interaction.gradient_renderer import GradientRenderer
from interaction.ring_band_renderer import RingBandRenderer
import numpy as np
import math

class MaxForceInteraction(BaseInteraction):
    @classmethod
    def default_config(cls):
        return {
            **default_weighting_config(),
            "colorA": {"value": Color(10, 10, 10), "type": "Color"},
            "colorB": {"value": Color(0, 0, 100), "type": "Color"},
            "colorC": {"value": Color(180, 0, 125), "type": "Color"},
            "colorD": {"value": Color(225, 0, 0), "type": "Color"},
            "smoothingWindowSize": {"value": 9, "type": "int"},
        }

    def __init__(self, name, device_mgr, buffer, mqtt, state_mgr):
        super().__init__(name, device_mgr, buffer, mqtt, state_mgr)
        self._init_renderers()
        self._setup_stores()

    def _setup_stores(self):
        self.store = {k:0 for k in self.device_mgr.get_selected_devices()}

    def _init_renderers(self):
        self.gradient = GradientRenderer(
            self.device_mgr,
            self.config["colorA"]["value"],
            self.config["colorB"]["value"],
            self.config["colorC"]["value"],
            self.config["colorD"]["value"],

        )
    
    def on_config(self, key, value):
        if "color" in key:
            self._init_renderers()
        if key == "smoothingWindowSize":
            self._compute_smoothing_window()
    
    def on_device_update(self):
        # Update the device manager with the latest configuration
        self._setup_stores()

    def _compute_smoothing_window(self):
        # Compute the smoothing window based on the configuration
        window_size = self.config["smoothingWindowSize"]["value"]
        if window_size <= 1:
            self.smoothing_window = [1]
        else:
            sigma = 1.0  # Adjust sigma to control spread; ~1 is reasonable for a 7-sample kernel

            x = np.linspace(-(window_size // 2), window_size // 2, window_size)
            self.smoothing_window = np.exp(-x**2 / (2 * sigma**2))

            # Normalize kernel to sum to 1
            self.smoothing_window /= self.smoothing_window.sum()

    def on_select(self):
        super().on_select()
        self._compute_smoothing_window()
        self._setup_stores()

    def update(self):
        # Fetch configuration parameters
        sample_window = self.config["window_s"]["value"]
        min_t = self.config["min_threshold"]["value"]
        max_t = self.config["max_threshold"]["value"]


        # Collect recent sensor vectors and magnitudes for selected devices

        for dev in self.device_mgr.get_selected_devices():
            mag_vals = self.buffer.get_recent(dev, "mag", sample_window)
            if not mag_vals:
                continue

            smoothed_vals = np.convolve(mag_vals, self.smoothing_window, mode='valid')
            avg_mag = np.mean(mag_vals) if len(mag_vals) > 0 else 0
            if(avg_mag > min_t and len(smoothed_vals) > 0):
                cur = self.store[dev] if dev in self.store else 0
                self.store[dev] = max(cur,np.max(mag_vals))                
            else: 
                if dev in self.store:
                    self.store.pop(dev)

        for dev in self.device_mgr.get_selected_devices():
            if dev in self.store:
                c_val = min(max(self.store[dev] / max_t, 0), 1)
                if np.isnan(c_val) or np.isinf(c_val):
                    c_val = 0
                self.gradient.render(dev, c_val)
            else:
                 self.gradient.render(dev, -1)

