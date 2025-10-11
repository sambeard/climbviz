import json

from interaction.base_renderer import Color  # or wherever Color is defined

class CustomJSONEncoder(json.JSONEncoder): # type: ignore
    def default(self, obj):
        if isinstance(obj, Color):
            return {k:v for k,v in zip("rgb",obj.rgb)}
        return super().default(obj)
    
def custom_json_hook(dct):
    if set(dct.keys()) == {"r", "g", "b"}:
        return Color(**dct)
    return dct

class StateManager:
    """
    Central state handler that maintains application-wide settings and parameters.
    Publishes updates over MQTT and listens for external changes.

    Supports hierarchical keys (e.g., interaction/active) and typed parameters.
    """

    def __init__(self, mqtt, base_topic="climbviz/state"):
        self._state = {}
        self._callbacks = {}  # path -> callable
        self._mqtt = mqtt
        self._base = base_topic

        # Subscribe to all state paths
        mqtt.subscribe(f"{self._base}/#", self._on_mqtt_message)

    def set(self, path, value):
        """
        Updates the state and publishes to MQTT.
        `path` is a '/'-delimited string, e.g., 'interaction/active'
        """
        self._assign_path(path, value)
        full_topic = f"{self._base}/{path}"
        payload = json.dumps(value, cls=CustomJSONEncoder)
        self._mqtt.publish(full_topic, payload)

    def get(self, path, default=None):
        """
        Retrieves a value from nested state.
        """
        return self._resolve_path(path, default)

    def register_callback(self, path, callback):
        """
        Registers a handler to be called when a particular state path is updated.
        """
        self._callbacks[path] = callback

    def register_param(self, type, name, param_name, value, value_type):
        """
        Registers a typed parameter for an interaction.
        """
        path = f"{type}/params/{name}/{param_name}"
        self.set(path, { "value": value, "type": value_type })

    def _assign_path(self, path, value):
        """
        Internal method to set nested dict values.
        """
        keys = path.split("/")
        target = self._state
        for key in keys[:-1]:
            target = target.setdefault(key, {})
        target[keys[-1]] = value

    def _resolve_path(self, path, default=None):
        """
        Internal method to get nested dict values.
        """
        keys = path.split("/")
        target = self._state
        for key in keys:
            if isinstance(target, dict) and key in target:
                target = target[key]
            else:
                return default
        return target

    def _on_mqtt_message(self, topic, payload_bytes):
        """
        Called when state message is received over MQTT.
        Updates local state and triggers any listeners.
        """
        try:
            path = topic[len(self._base) + 1:]
            value = json.loads(payload_bytes.decode("utf-8"), object_hook=custom_json_hook)
            self._assign_path(path, value)

            if path in self._callbacks:
                self._callbacks[path](value)
        except Exception as e:
            print(f"[StateManager] Failed to handle message: {e}")
