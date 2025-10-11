# climbviz/main.py

"""
Revised entry point for the ClimbViz application using Tkinter.
Initializes core logic modules, state manager, and launches the GUI.
"""

import json
import argparse
from core.mqtt_manager import MQTTManager
from core.device_manager import DeviceManager
from core.interaction_engine import InteractionEngine
from core.analysis_engine import AnalysisEngine
from core.playback_engine import PlaybackEngine
from core.recorder import Recorder
from buffer.devicebuffer import DeviceBuffer
from buffer.recordingbuffer import RecordingBuffer
from core.recorder import Recorder
from core.state_manager import StateManager
from ui.app import ClimbApp


def start(config_file="config.json"):
    # Load configuration
    with open(config_file) as f:
        config = json.load(f)

    # Initialize MQTT and start client
    mqtt = MQTTManager(**config["mqtt"])
    mqtt.start()

    # Initialize application state manager
    state = StateManager(mqtt)

    # and buffer for device data
    buffer = DeviceBuffer()
    recording_buffer = RecordingBuffer()


    # Core components
    recorder = Recorder(recording_buffer, state)
    device_mgr = DeviceManager(config, mqtt, state, buffer,recorder)
    interaction_engine = InteractionEngine(config,device_mgr, buffer, mqtt, state)
    analysis_engine = AnalysisEngine(config,device_mgr, mqtt, state)
    playback_engine = PlaybackEngine(mqtt, state)

    # Launch the full GUI using Tkinter
    app = ClimbApp(config, mqtt, device_mgr, buffer, interaction_engine, analysis_engine, playback_engine, recorder, state)
    app.mainloop()

    mqtt.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ClimbViz Application")
    parser.add_argument("--config", type=str, default="config.local.json", help="Path to the configuration file")
    args = parser.parse_args()
    
    start(config_file=args.config)