from interaction.base_renderer import BaseRenderer, Color

class GradientRenderer(BaseRenderer):
    def __init__(self, device_manager, *colors, n_leds=25):
        super().__init__(device_manager, n_leds)
        self.colors = colors
        while len(self.colors) < 2:
            self.colors = [Color(0, 0, 0), * self.colors]
        self.n_cols = len(self.colors)

    def get_lerped_color(self, t: float, brightness):
        i = int(t * (self.n_cols - 1))
        f = t * (self.n_cols - 1) - i
        if (i >= self.n_cols - 1):
            return self.colors[-1]
        if (i < 0):
            return Color(0,0,0)
        color_a, color_b = self.colors[i], self.colors[i+1]
        color = color_a.lerp_color(color_b, f)
        if(brightness != 1.0):
            color = color.with_brightness(brightness)
        return color


    def compute_leds(self, t: float, brightness=1.0):
        color = self.get_lerped_color(t,brightness)
        return [color] * self.n_leds