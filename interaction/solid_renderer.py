from interaction.base_renderer import Color, BaseRenderer

class SolidColorRenderer(BaseRenderer):
    def __init__(self, device_manager, color: Color, n_leds=25):
        super().__init__(device_manager, n_leds)
        self.color = color

    def compute_leds(self):
        return [ self.color ] * self.n_leds