import time
import json
import math
import threading
import random
import paho.mqtt.client as mqtt

class MockDevice:
    """
    A simulated sensor device that periodically sends data to the MQTT broker,
    pretending to be a real veloring sensor node.
    """
    def __init__(self, device_id, mqtt_client, interval=0.1):
        self.device_id = device_id
        self.mqtt = mqtt_client
        self.interval = interval
        self.running = False
        self.paused = False
        self._phase = 0.

    def start(self):
        self.running = True
        self._setup()
        thread = threading.Thread(target=self._loop)
        thread.daemon = True
        thread.start()

    def _setup(self):
        self._phase = random.uniform(0, 2 * math.pi)

    def toggle_pause(self):
        self.paused = not self.paused
        self._handle_pause(self.paused)

    def _handle_pause(self, paused):
        pass  # Placeholder for any pause handling logic

    def stop(self):
        self.running = False

    def _loop(self):
        while self.running:
            if self.paused:
                time.sleep(0.1)
                continue
            self._wait_till_next()
            t = time.time()
            payload = self._gen_payload(t)
            if payload is None:
                continue
            topic = f"velo-ring/{self.device_id}/data/features"
            self.mqtt.publish(topic, json.dumps(payload))

    def _wait_till_next(self):
        time.sleep(self.interval)

    def _gen_payload(self, t):
        return {
            "time": int(t * 1000),
            "mag": 1.0 + math.sin(t + self._phase) * 0.1,
            "phi": math.sin(t / 3.0 + self._phase),
            "theta": math.cos(t / 2.0 + self._phase),
            "x": random.uniform(-1, 1),
            "y": random.uniform(-1, 1),
            "z": random.uniform(-1, 1)
        }


def run_mock_devices(broker_host, num_devices=3):
    # setup mqtt client
    client = mqtt.Client()
    client.connect(broker_host, 1883, 60)
    client.loop_start()

    # create and start mock devices
    mocks = []
    for i in range(num_devices):
        dev_id = f"mock-{i+1}"
        mock = MockDevice(dev_id, client)
        mock.start()
        mocks.append(mock)

    # run the devices until interrupted
    print(f"Started {num_devices} mock devices. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping mock devices...")
        for m in mocks:
            m.stop()
        client.loop_stop()


if __name__ == "__main__":
    run_mock_devices("192.168.50.69", num_devices=3)
