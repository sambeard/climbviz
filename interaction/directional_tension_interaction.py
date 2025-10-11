from interaction.base_interaction import BaseInteraction, default_weighting_config
from interaction.base_renderer import Color
from interaction.gradient_renderer import GradientRenderer
from interaction.ring_band_renderer import RingBandRenderer
import numpy as np
import math

class DirectionalTensionInteraction(BaseInteraction):
    @classmethod
    def default_config(cls):
        return {
            **default_weighting_config(),
            "colorGradientA": {"value": Color(15, 15, 15), "type": "Color"},
            "colorGradientB": {"value": Color(135, 125, 25), "type": "Color"},
            "colorGradientC": {"value": Color(200, 150, 0), "type": "Color"},
            "colorGradientD": {"value": Color(250, 0, 0), "type": "Color"},
            "colorBand": {"value": Color(255, 0, 0), "type": "Color"},
            "tangent_threshold": {"value": 0.25, "type": "float"}
        }

    def __init__(self, name, device_mgr, buffer, mqtt, state_mgr):
        super().__init__(name, device_mgr, buffer, mqtt, state_mgr)
        self._init_renderers()

    def _init_renderers(self):
        self.gradient = GradientRenderer(
            self.device_mgr,
            self.config["colorGradientA"]["value"],
            self.config["colorGradientB"]["value"],
            self.config["colorGradientC"]["value"],
            self.config["colorGradientD"]["value"],
        )
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
        threshold = self.config["tangent_threshold"]["value"]

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
        n_factor = min(max(0.0, norm / (upper_limit*2)), 1.0)

        # For each device, compare its force direction to the resultant
        for dev, vec in device_vecs.items():
            
            differential = vec
            vnorm = np.linalg.norm(differential)

            if vnorm == 0:
                continue
            unit_vec = differential / vnorm
            dot = np.clip(np.dot(unit_vec, resultant), -1, 1)
            tangential_factor = 1-abs(dot)
            vnorm = min(1.0, max(0.0, (vnorm - min_t) / upper_limit))

            # If tangential to the resultant, render a directional band
            if tangential_factor >= threshold:
                phi_angle = math.atan2(vec[1], vec[0]) / (2 * math.pi)
                phi_angle = (phi_angle + 1) % 1.0  # normalize to [0, 1]
                width = .15 + .85*(1 - tangential_factor)  # narrower if stronger force
                # print(n_factor, tangential_factor, width)
                bgcol = self.gradient.get_lerped_color(n_factor, brightness=.3)
                self.band.render(dev, center=phi_angle, width=width, brightness=vnorm, bg_color=bgcol, blend= tangential_factor)
            # If perpendicular, render with gradient based on magnitude
            else:
                br = min(1.0, max(0.0, np.linalg.norm(vec) / upper_limit))
                self.gradient.render(dev, n_factor, brightness=br)
