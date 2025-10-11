from buffer.recordingbuffer import RecordingBuffer

class Recorder:
    def __init__(self, recording_buffer, state):
        self.buffer = recording_buffer
        self.state = state
        self.recording = False

    def start(self):
        self.buffer.data.clear()
        self.recording = True
        self.state.set("recording/active", True)

    def stop(self):
        self.recording = False
        self.state.set("recording/active", False)

    def update(self, device_id, time, feature_data):
        if self.recording:
            self.buffer.update(device_id, time, feature_data)

    def export_csv(self, path):
        self.buffer.export_csv(path)    