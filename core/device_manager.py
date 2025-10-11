import ast
import json
from utils import deep_merge

class DeviceManager:
    """
    Manages known devices, tracks which are selected, and provides methods
    for sending commands like calibration over MQTT. Synchronizes with
    shared application state.
    """
    used_features = ["mag", "phi", "theta", "x", "y", "z"]

    def __init__(self, config, mqtt_manager, state_manager, buffer, recorder):
        self._extract_config(config)
        self.mqtt = mqtt_manager
        self.state = state_manager
        self.buffer = buffer
        self.recorder = recorder
        self.devices = set()
        self.selected = set()

        self.state.register_callback("devices/selected", self._on_selected_updated)
        selected_from_state = self.state.get("devices/selected", [])
        self.selected.update(selected_from_state)
        self.init_subscriptions()

    def _extract_config(self, config):
        self.global_config = config.get("global_config", {})
        self.device_configs = {
            dev["id"]: dev.get("config", {}) for dev in config.get("devices", [])
        }

    def init_subscriptions(self):
        """
        Subscribes to relevant MQTT topics and attaches message handler.
        """
        self.mqtt.subscribe_device_topics(self._on_mqtt_message)

    def _on_mqtt_message(self, topic, payload_bytes):
        topic_parts = topic.split("/")
        if len(topic_parts) < 3:
            return

        device_id = topic_parts[1]

        if topic.endswith("/config/id") or not device_id in self.devices: 
            self._register_device(device_id)

        elif topic.endswith("/data/features"):
            try:
                payload = ast.literal_eval(payload_bytes.decode("utf-8"))
                self._handle_feature_data(device_id, payload)
            except Exception as e:
                print(f"[DeviceManager] Failed to parse features from {device_id}: {e}")

    def _apply_device_config(self, device_id):
        device_specific = self.device_configs.get(device_id, {})
        merged = deep_merge(self.global_config, device_specific)
        self._send_nested_config(device_id, merged)

    def _send_nested_config(self, device_id, config, path=""):
        for key, val in config.items():
            subpath = f"{path}/{key}" if path else key
            if isinstance(val, dict):
                self._send_nested_config(device_id, val, subpath)
            else:
                topic = f"velo-ring/{device_id}/config/{subpath}"
                self.mqtt.publish(topic, bytes(str(val),encoding='utf-8'))

    def _send_config(self, device_id, key, value):
        topic = f"velo-ring/{device_id}/config/{key}"
        self.mqtt.publish(topic, json.dumps(value))

    def send_led_data(self, device_id, color_buf):
        topic = f"velo-ring/{device_id}/data/led"
        self.mqtt.publish(topic, str(color_buf))

    def send_cmd(self, command):
        """
        Sends a command to all devices via velo-ring/cmd.
        """
        print(f"[DeviceManager] Sending CMD: {command}")
        self.mqtt.publish("velo-ring/cmd", command.encode("utf-8"))

    def toggle_device(self, device_id):
        if device_id in self.selected:
            self.selected.remove(device_id)
        else:
            self.selected.add(device_id)
        self._update_state()

    def toggle_auto_calibrate(self):
        current = self.state.get("devices/auto_calibrate", False)
        new_state = not current
        self.state.set("devices/auto_calibrate", new_state)

        for dev in self.devices:
            topic = f"velo-ring/{dev}/config/calibration/auto_calibrate"
            self.mqtt.publish(topic, str(new_state))

    def _update_state(self):
        self.state.set("devices/selected", list(self.selected))

    def get_selected_devices(self):
        return list(self.selected)
    
    def get_all_devices(self):
        return list(self.devices)

    def send_calibrate_command(self, auto=True):
        for dev in self.devices:
            topic = f"velo-ring/{dev}/config/calibration/auto_calibrate"
            self.mqtt.publish(topic, str(auto).encode('utf-8'))

    def start_manual_calibration(self):
        for dev in self.devices:
            topic = f"velo-ring/cmd"
            self.mqtt.publish(topic, b"calibrate")

    def _extract_time(self, payload):
        return payload.get("time", -1) /1000.0 + self.state.get("time_offset", 10)

    def _handle_feature_data(self, device_id, payload):
        """
        Passes parsed feature data to the rolling buffer.
        """
        time = self._extract_time(payload)
        self.buffer.update(device_id, time, payload)
        if self.recorder and self.state.get("recording/active", True):
            self.recorder.update(device_id, time, payload)

# === PATCHED BEHAVIOR ===

# ... previous content of device_manager.py ...

    def _on_selected_updated(self, selected_list):
        old_selected = self.selected
        self.selected = set(selected_list)

        for dev in self.devices:
            was_selected = dev in old_selected
            now_selected = dev in self.selected

            if now_selected and not was_selected:
                self._apply_device_config(dev)  # newly selected
            elif was_selected and not now_selected:
                self.send_led_data(dev, [0, 0, 0] * 25)  # blank out

    def _register_device(self, device_id):
        print(f"[DeviceManager] Registered new device: {device_id}")
        self.devices.add(device_id)
        self._apply_device_config(device_id)

        if device_id not in self.device_configs:
            self.device_configs[device_id] = {}
            self._update_state()
