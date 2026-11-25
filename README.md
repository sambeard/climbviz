# ClimbViz

ClimbViz is the central controller for **VeloRing** sensor devices mounted on a climbing wall. It discovers devices over MQTT, pushes configuration to them, plots their live sensor data, and drives each ring's LEDs through **interactions** (live feedback) and **analyses** (post-hoc feedback from a recording).

The VeloRing firmware lives in a separate repository and isn't needed here. ClimbViz only talks to the devices over MQTT; the topics and data it uses are described [below](#the-data).

---

## Requirements

- Python 3.11 (other 3.x versions will probably work, but 3.11 is the tested one)
- Tkinter (bundled with the python.org installers; on Linux, install `python3-tk`)
- An MQTT broker that both this machine and the VeloRings can reach

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Network setup

> **The controller, the VeloRings, and the MQTT broker must all be on the same network.**

The devices connect to the broker by themselves. ClimbViz connects to that same broker and does everything through it, so it never talks to a device directly. If the controller can't see device messages, the problem is almost always the network or the broker, not ClimbViz. Please do make sure that the power is plugged in for both the IICW server as well as the devices (should be a power adapter somewhere at the back of the wall connected to the devices via red/black wires).

### IICW setup

In the IICW setup, the server on the local network runs the MQTT broker. It must be configured to run that broker. The host, port, and credentials are in [`config.iicw.json`](config.iicw.json) under `"mqtt"`.

### Local setup

[`config.local.json`](config.local.json) points to a broker on `localhost:1883`. This is useful for development with [mock devices](#mock-sensors) or [playback](#playback), with no hardware involved. Any broker works, e.g. [Mosquitto](https://mosquitto.org/):

```bash
mosquitto -v
```

### Debugging the connection

Debug with an MQTT client. Subscribe to everything and check what's actually on the wire:

```bash
mosquitto_sub -h <host> -p 1883 -u <user> -P <password> -t '#' -v
```

You should see `velo-ring/<id>/data/features` messages coming in from every powered device. If you don't, ClimbViz won't see them either. A GUI client such as [MQTT Explorer](https://mqtt-explorer.com/) also works **really** well for this.

## Running

```bash
# IICW (remote broker)
python main.py --config config.iicw.json

# Local broker (default)
python main.py --config config.local.json
```

In VS Code, the launch configurations **Run ClimbViz - Remote** and **Run ClimbViz - Local** in `.vscode/launch.json` do the same.

**Startup can take a minute.** Once connected, devices should auto-discover and appear under **Devices** in the left panel. If a device doesn't show up, press **Identify Devices**. This broadcasts an identification challenge on `velo-ring/cmd`, and every device that hears it announces itself.

## Using the UI

### Main window

The left panel contains:

| Control | What it does |
|---|---|
| **Devices** | One checkbox per discovered device. Only *selected* devices are plotted and driven by interactions/analyses. Selecting a device pushes its config to it; deselecting blanks its LEDs. |
| **Feature** | Which feature to plot (`mag`, `phi`, `theta`, `x`, `y`, `z`). |
| **Interaction / Analysis** | Switches modes. *Interaction* runs a live LED loop on incoming data. *Analysis* loads a recording from `data/` and renders a single result to the LEDs. |
| **Time Offset (s)** | Shifts device timestamps to line up with the controller's clock in the plot. |
| **Calibration** | Toggle on-device auto-calibration, or trigger a manual calibration. Calibration is just actually offset adjustment (e.g. zeroing)|
| **Global Device Commands** | Broadcast `identify`, `start`, `stop`, `calibrate`, `sync` (time) or `reset` to all devices. |

The right side plots the selected feature for the selected devices: a rolling 30 s window in Interaction mode, or the full recording in Analysis mode.

### Tools menu

- **Interaction Config… / Analysis Config…**: edit the numeric parameters (thresholds, windows) of the active interaction or analysis at runtime.
- **Recording Tools…**: start/stop recording incoming data and export it as CSV. Put the exports in `data/` to use them in Analysis mode or Playback.
- **Playback Tools…**: replay a recorded CSV over MQTT as if the devices were live. Good for developing interactions without a wall.
- **Mock Sensors…**: spawn fake devices that publish synthetic data.
- **Device Grid…**: a board view (15×11 by default) showing where each device sits on the wall, based on the `coordinates` in the config.

### Calibration & constants

All calibration values, thresholds, and constants in the configs and interactions (coefficients, auto-calibrate limits, `min_threshold`/`max_threshold`, colors, etc.) were tuned by hand and are not rigorously derived. **Feel free to change them** if other values suit your setup better.

## Configuration

Config files are JSON. The important keys:

```jsonc
{
  "DEBUG": true,                 // if true, exceptions in the interaction loop crash loudly instead of being logged
  "mqtt": { "host": "...", "port": 1883, "username": "...", "password": "..." },
  "features": ["mag", "phi", "theta", "x", "y", "z"],   // features selectable in the plot
  "plot_window": 30,             // seconds of history in the live plot
  "future_margin": 5,            // seconds of empty space right of "now"

  "global_config": { ... },      // pushed to EVERY device on discovery/selection
  "devices": [                   // per-device overrides, deep-merged over global_config
    { "id": "2454855314760098278",
      "config": { "coordinates": { "x": 0, "y": 5 },
                  "calibration": { "coefficients": 0.0014 } } }
  ],

  "board": { "rows": 15, "cols": 11 },
  "route_dir": "routes/"
}
```

When a device is discovered or selected, ClimbViz merges `global_config` with that device's entry and publishes each leaf value to its own topic. For example, `calibration.coefficients` goes to `velo-ring/<id>/config/calibration/coefficients`. Devices not listed in `devices` simply get the global config.

To add a new device, power it on, copy its ID from the Devices list (or from MQTT), and add an entry with its wall coordinates.

## The data

### MQTT topics

| Topic | Direction | Payload |
|---|---|---|
| `velo-ring/<id>/config/id` | device → controller | Announcement; triggers registration |
| `velo-ring/<id>/data/features` | device → controller | Feature sample (see below) |
| `velo-ring/<id>/config/<path>` | controller → device | One config value, e.g. `calibration/auto_calibrate` |
| `velo-ring/<id>/data/led` | controller → device | 25 LEDs × 3 bytes, **GRB** order |
| `velo-ring/cmd` | controller → all | `identify`, `start`, `stop`, `calibrate`, `sync`, `reset` |
| `climbviz/state/#` | controller ↔ controller | Application state (active interaction, params, selection…) as JSON |

### Feature samples

Each device streams samples (around 50 Hz by default, `measure_fps`) like:

```json
{ "time": 1744379484480, "x": 0.59, "y": -0.24, "z": 0.40, "mag": 0.76, "phi": 0.69, "theta": 0.36 }
```

| Field | Meaning |
|---|---|
| `time` | Device timestamp in milliseconds |
| `x`, `y`, `z` | Force vector components measured by the ring (calibrated, arbitrary units) |
| `mag` | Magnitude of the force vector, i.e. how hard the hold is loaded |
| `phi` | Direction of the force in the wall plane (angle) |
| `theta` | Angle of the force relative to the wall plane, i.e. how much it pulls outward vs. along the wall |

Units depend on the calibration coefficients, so treat absolute values as relative. The default "is this hold being used" threshold is `mag > 2.5`.

### Recordings

Recordings are CSV files in `data/`, one row per sample:

```csv
device_id,time,x,y,z,mag,phi,theta
3914011698423488998,1744379484.48,0.5956993,-0.239633,0.404002,0.7586166,0.6891291,0.3575326
```

`time` is in seconds. The repo includes several recordings from IICW sessions that you can use to try things out.

## Architecture

```
main.py              wires everything together and starts the Tk app
core/
  mqtt_manager.py    thin paho-mqtt wrapper (publish / subscribe with callbacks)
  state_manager.py   hierarchical app state, mirrored to climbviz/state/#
  device_manager.py  discovery, selection, config push, LED + command publishing
  interaction_engine.py  runs the active interaction in a loop (~15 FPS)
  analysis_engine.py     runs the active analysis once over a loaded recording
  recorder.py        records incoming samples into a RecordingBuffer
  playback_engine.py replays a CSV as fake devices
  mocking.py         synthetic MockDevice
buffer/              in-memory per-device feature buffers (live and recorded)
interaction/         interactions, analyses and LED renderers
ui/                  Tkinter windows
utils/               helpers (deep_merge)
```

Data flows like this:

```
VeloRing ──features──▶ MQTT ──▶ DeviceManager ──▶ DeviceBuffer ──▶ InteractionEngine ──▶ Interaction
                                      │                                                     │
                                      └──▶ Recorder ──▶ CSV ──▶ AnalysisEngine ──▶ Analysis  │
                                                                                    │       │
VeloRing ◀──────────── LED bytes ◀──── MQTT ◀──── Renderer ◀────────────────────────┴───────┘
```

All shared settings go through `StateManager`. Calling `state.set("interaction/active", ...)` updates local state *and* publishes it, so other components (or another ClimbViz instance) can react.

## Contributing

### Adding an interaction

An interaction reads recent data from the live buffer every frame and renders LEDs for each selected device in real time(ish).

1. Create `interaction/my_interaction.py`:

   ```python
   from interaction.base_interaction import BaseInteraction, default_weighting_config
   from interaction.base_renderer import Color
   from interaction.gradient_renderer import GradientRenderer

   class MyInteraction(BaseInteraction):
       @classmethod
       def default_config(cls):
           # Every entry shows up in "Interaction Config…" and is stored in state
           return {
               **default_weighting_config(),        # min_threshold, max_threshold, window_s
               "colorLow":  {"value": Color(0, 20, 0), "type": "Color"},
               "colorHigh": {"value": Color(255, 0, 0), "type": "Color"},
           }

       def __init__(self, *args):
           super().__init__(*args)
           self._init_renderer()

       def _init_renderer(self):
           self.renderer = GradientRenderer(self.device_mgr,
                                            self.get_config("colorLow"),
                                            self.get_config("colorHigh"))

       def on_config(self, key, value):
           if key.startswith("color"):
               self._init_renderer()

       def update(self):
           window = self.get_config("window_s")
           for dev in self.device_mgr.get_selected_devices():
               mags = self.buffer.get_recent(dev, "mag", window)
               if not mags:
                   continue
               t = sum(mags) / len(mags) / self.get_config("max_threshold")
               self.renderer.render(dev, min(1.0, max(0.0, t)))
   ```

2. Register it in `core/interaction_engine.py` in the `self.interactions` dict. **The key and the `name` argument must match**, because the name is used as the state path for its parameters:

   ```python
   "MyInteraction": MyInteraction("MyInteraction", self.device_mgr, self.buffer, self.mqtt, self.state),
   ```

It will now appear in the main window's interaction list.

### Adding an analysis

Same pattern, but subclass `BaseAnalysis` (`interaction/base_analysis.py`), implement `calculate()` instead of `update()`, and register it in `core/analysis_engine.py`. `self.get_feature(dev, "mag")` returns the full recorded series for a device. `calculate()` runs once when the analysis or recording is selected, not in a loop.

### Adding a renderer

Renderers turn a value into 25 LED colors. Subclass `BaseRenderer` (`interaction/base_renderer.py`) and implement `compute_leds(...)` to return a list of 25 `Color`s. `render(device_id, ...)` handles the GRB byte conversion and publishing. See `solid_renderer.py`, `gradient_renderer.py` and `ring_band_renderer.py` for examples.

### Parameter types

The `"type"` in `default_config` decides how the config windows parse input. Use `"float"`, `"int"`, or `"Color"`. Colors are stored in state as `{"r":…, "g":…, "b":…}`. Note that the config windows can currently only edit `float` and `int` values. Colors still need to be changed in code (or by publishing to the state topic).

### Development tips

- Develop against `config.local.json` with **Mock Sensors** or **Playback** of one of the CSVs in `data/`. No wall needed.
- Keep `"DEBUG": true` while developing so errors in your `update()` surface instead of being swallowed by the loop.
- Watch `climbviz/state/#` and `velo-ring/+/data/led` with `mosquitto_sub` to see exactly what your code is sending.
- There's no test suite. Check changes by running the app against playback data.

### Workflow

1. Make a fork based off `main`.
2. Keep changes focused. If you change tuned constants, note why in the commit message.
3. Open a pull request describing what you changed and how you tested it (e.g. which recording you played back).
4. Let me know what kind of cool stuff you make.
