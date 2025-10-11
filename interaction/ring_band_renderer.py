from interaction.base_renderer import BaseRenderer, Color

class RingBandRenderer(BaseRenderer):
    def __init__(self, device_manager, color: Color, n_leds=25):
        super().__init__(device_manager, n_leds)
        self.color = color

    def compute_leds(self, center: float, width: float, brightness: float = 1.0, bg_color=None, blend = 1.0):
        bg = Color(0, 0, 0) if bg_color is None else bg_color
        pixels = [bg] * self.n_leds
        half_width = width * self.n_leds / 2
        center_idx = int(center * self.n_leds)
        fg = bg.lerp_color(self.color, blend)
        for i in range(self.n_leds):
            dist = abs((i - center_idx + self.n_leds) % self.n_leds - self.n_leds // 2)
            if dist < half_width:
                pixels[i] = Color.lerp_color(fg, bg, dist / half_width)
        if(brightness != 1.0):
            pixels = [c.with_brightness(brightness) for c in pixels]
        return pixels
