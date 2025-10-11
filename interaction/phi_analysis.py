import pandas as pd
from interaction.base_interaction import default_weighting_config
from interaction.base_analysis import BaseAnalysis
from interaction.base_renderer import BaseRenderer, Color


class PhiBinRenderer(BaseRenderer):
    def __init__(self, device_manager, color_a, color_b, n_leds=25):
        super().__init__(device_manager, n_leds)
        self.color_a: Color= color_a
        self.color_b : Color= color_b

    def compute_leds(self, bins):
        buffer = [Color(0,0,0)]*self.n_leds
        if(len(bins) != self.n_leds):
            return buffer
        else:
            for i,b in enumerate(bins):
                if b == 0:
                    continue
                bv = min(1,max(0,b))
                buffer[i] = self.color_a.lerp_color(self.color_b, bv)
            return buffer


class PhiAnalysis(BaseAnalysis):

    def __init__(self, name, device_mgr, mqtt, state_mgr):
        super().__init__(name, device_mgr, mqtt, state_mgr)

    @classmethod
    def default_config(cls):
        return {
            **default_weighting_config(min_t=5),
            "colorA": {"value": Color(10, 10, 10), "type": "Color"},
            "colorB": {"value": Color(0, 0, 255), "type": "Color"},

        }
    
    def on_config(self, key: str, value):
        """Called when a config value is updated. Override as needed."""
        super().on_config(key, value)
        self._init_renderer()

    def _init_renderer(self):
        self.renderer = PhiBinRenderer(
            self.device_mgr,
            self.config["colorA"]["value"],
            self.config["colorB"]["value"],
        )

    def calculate(self):
        min_t = self.get_config("min_threshold") if "min_threshold" in self.config else float('inf')
        for dev in self.device_mgr.get_all_devices():
            if not dev in self.device_mgr.selected or not self.buffer or not dev in self.buffer.devices:
                self.renderer.render(dev, [])
                continue
            mags = self.get_feature(dev, "mag")
            phis = self.get_feature(dev, "phi")
            times = self.get_feature(dev, "time")
            _df = pd.DataFrame({"mag": mags, "phi": phis, "time": times})
            _df.set_index("time", inplace=True)
            _df = _df[_df["mag"].rolling(15).min() > min_t]

            if _df.empty:
                self.renderer.render(dev, [])
                continue
            phis_t = _df["phi"].values
            phi_discreet = [int(((phi+.5)%1)*self.renderer.n_leds)for phi in phis_t]
            phi_bins = [0] * self.renderer.n_leds
            for s in phi_discreet:
                phi_bins[s] +=1
            phi_bins_normalized = [s / len(phi_discreet) for s in phi_bins]
            self.renderer.render(dev, phi_bins_normalized)