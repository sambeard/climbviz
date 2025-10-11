
import tkinter as tk
import time
import os

def open_record_window(master, data_path, recorder, state_manager):
    """
    Window to control data recording and manage the output filename.
    Stores file path in shared state and supports export/load cycles.
    """
    win = tk.Toplevel(master)
    win.title("Recording Tools")
    win.geometry("340x240")

    default_file = state_manager.get("recording/filename", "recording.json")
    tk.Label(win, text="Output Filename (no ext)").pack(pady=5)
    filename_var = tk.StringVar(value=default_file.replace(".json", ""))
    filename_entry = tk.Entry(win, textvariable=filename_var)
    filename_entry.pack(fill=tk.X, padx=10)

    def start():
        recorder.start()
        state_manager.set("recording/active", True)
        tk.Label(win, text="Recording started at " + time.strftime('%H:%M:%S')).pack() # type: ignore

    def stop():
        recorder.stop()
        frames = recorder.buffer.data
        state_manager.set("recording/active", False)
        tk.Label(win, text=f"Stopped: {len(frames)} frames").pack()

    def export():
        base = filename_var.get()
        if not base.endswith(".csv"):
            base += ".csv"
        csv_path = os.path.join(data_path, base+".csv")
        recorder.export_csv(csv_path)
        state_manager.set("recording/filename", base)
        tk.Label(win, text=f"Saved to {csv_path}").pack()

    tk.Button(win, text="Start Recording", command=start).pack(pady=5)
    tk.Button(win, text="Stop Recording", command=stop).pack(pady=5)
    tk.Button(win, text="Export CSV", command=export).pack(pady=5)
