import paho.mqtt.client as mqtt

class MQTTManager:
    """
    Handles connection to MQTT broker and provides simple publish/subscribe
    interface for the rest of the application.
    """
    def __init__(self, host, port, username=None, password=None):
        self.client = mqtt.Client()
        if username and password:
            self.client.username_pw_set(username, password)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.callbacks = {}  # topic -> callback
        self.host = host
        self.port = port

    def _on_connect(self, client, userdata, flags, rc):
        print("Connected to MQTT broker:", rc)
        for topic in self.callbacks:
            self.client.subscribe(topic)

    def _on_message(self, client, userdata, msg):
        for topic, callback in self.callbacks.items():
            if mqtt.topic_matches_sub(topic, msg.topic):
                callback(msg.topic, msg.payload)

    def subscribe(self, topic, callback):
        """
        Subscribes to a topic and registers a callback.
        """
        self.callbacks[topic] = callback
        self.client.subscribe(topic)

    def publish(self, topic, payload):
        """
        Publishes a message to a topic.
        """
        self.client.publish(topic, payload)

    def subscribe_device_topics(self, callback):
        """
        Subscribes to all topics related to device discovery and data.
        """
        topics = [
            "velo-ring/+/config/id",
            "velo-ring/+/config/pad",
            "velo-ring/+/config/all_features",
            "velo-ring/+/data/features"
        ]
        for topic in topics:
            self.subscribe(topic, callback)

    def start(self):
        self.client.connect(self.host, self.port, keepalive=60)
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
