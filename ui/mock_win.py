import tkinter as tk
from core.mocking import MockDevice

_running_mocks = []

def open_mock_window(master, mqtt_manager, state_manager):
    """
    Opens a window to configure and launch mock sensor devices.
    Uses shared state to store settings like device count and interval.
    """
    win = tk.Toplevel(master)
    win.title("Mock Sensors")
    win.geometry("800x500")

    default_count = state_manager.get("mock/count", 3)
    default_interval = state_manager.get("mock/interval", 0.1)

    tk.Label(win, text="Number of Mock Devices").pack(pady=5)
    count_var = tk.StringVar(value=str(default_count))
    count_entry = tk.Entry(win, textvariable=count_var)
    count_entry.pack()

    tk.Label(win, text="Send Interval (seconds)").pack(pady=5)
    interval_var = tk.StringVar(value=str(default_interval))
    interval_entry = tk.Entry(win, textvariable=interval_var)
    interval_entry.pack()

    def start_mocks():
        global _running_mocks
        stop_mocks()

        try:
            count = int(count_var.get())
            interval = float(interval_var.get())
        except ValueError:
            tk.Label(win, text="Invalid values!").pack()
            return

        state_manager.set("mock/count", count)
        state_manager.set("mock/interval", interval)

        for i in range(count):
            dev_id = f"mock-{i+1}"
            mock = MockDevice(dev_id, mqtt_manager.client, interval=interval)
            mock.start()
            _running_mocks.append(mock)

        tk.Label(win, text=f"Started {count} mock devices.").pack()

    def stop_mocks():
        global _running_mocks
        for mock in _running_mocks:
            mock.stop()
        _running_mocks.clear()
        tk.Label(win, text="Stopped all mocks.").pack()

    tk.Button(win, text="Start Mocks", command=start_mocks).pack(pady=5)
    tk.Button(win, text="Stop Mocks", command=stop_mocks).pack(pady=5)
