from interaction.base_interaction import BaseInteraction, default_weighting_config
from interaction.base_renderer import Color
from interaction.gradient_renderer import GradientRenderer
import numpy as np

class TensionInteraction(BaseInteraction):
    @classmethod
    def default_config(cls):
        return {
            **default_weighting_config(),
            "colorRelaxed": {"value": Color(0, 100, 0), "type": "Color"},
            "colorTense": {"value": Color(255, 0, 0), "type": "Color"},
        }

    def __init__(self, name, device_mgr, buffer, mqtt, state_mgr):
        super().__init__(name, device_mgr, buffer, mqtt, state_mgr)
        self._init_renderer()

    def _init_renderer(self):
        self.renderer = GradientRenderer(
            self.device_mgr,
            self.config["colorRelaxed"]["value"],
            self.config["colorTense"]["value"]
        )

    def on_config(self, key, value):
        if key in ["colorRelaxed", "colorTense"]:
            self._init_renderer()

    def update(self):
        window = self.config["window_s"]["value"]
        min_t = self.config["min_threshold"]["value"]

        device_vecs = {}
        device_mags = {}

        for dev in self.device_mgr.get_selected_devices():
            x_vals = self.buffer.get_recent(dev, "x", window)
            y_vals = self.buffer.get_recent(dev, "y", window)
            mag_vals = self.buffer.get_recent(dev, "mag", window)

            if not x_vals or not y_vals or not mag_vals:
                continue

            avg_x = sum(x_vals) / len(x_vals)
            avg_y = sum(y_vals) / len(y_vals)
            avg_mag = sum(mag_vals) / len(mag_vals)

            if avg_mag < min_t:
                continue

            device_vecs[dev] = np.array([avg_x, avg_y])
            device_mags[dev] = avg_mag

        # Compute resultant force direction
        total_force = sum(vec * device_mags[dev] for dev, vec in device_vecs.items())
        norm = np.linalg.norm(total_force)
        if norm == 0:
            return
        resultant = total_force / norm

        for dev, vec in device_vecs.items():
            vnorm = np.linalg.norm(vec)
            if vnorm == 0:
                continue

            alignment = np.dot(vec / vnorm, resultant)
            tension_score = (1 - alignment) / 2.0  # 0=aligned, 1=tension
            tension_score = np.clip(tension_score, 0, 1)
            self.renderer.render(dev, tension_score)
