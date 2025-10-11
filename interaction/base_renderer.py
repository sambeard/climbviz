from dataclasses import dataclass

@dataclass
class Color:
    r: int
    g: int
    b: int

    @property
    def rgb(self):
        return (self.r, self.g, self.b)

    @property
    def grb(self):
        return (self.g, self.r, self.b)
    
    def lerp_color(self, other, t):
        return Color(*(int((1 - t) * a + t * b) for a, b in zip(self.rgb, other.rgb)))
    
    def with_brightness(self, brightness):
        brightness = max(0, min(brightness, 1))
        return Color(*(int(v * brightness) for v in self.rgb))

class BaseRenderer:
    def __init__(self, device_manager, n_leds=25):
        self.device_manager = device_manager
        self.n_leds = n_leds

    @classmethod
    def to_bytes(cls, colors: list[Color]):
        return bytes([v for c in colors for v in c.grb])

    def send(self, device_id, buffer):
        self.device_manager.send_led_data(device_id, buffer)

    def render(self, device_id, *args, **kwargs):
        buffer = self.compute_leds(*args, **kwargs)
        self.send(device_id, self.to_bytes(buffer))

    def compute_leds(self, *args, **kwargs):
        raise NotImplementedError("Implement in subclass.")
