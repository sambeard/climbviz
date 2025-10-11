import tkinter as tk
from tkinter import ttk
from core.playback_engine import PlaybackEngine
from os import listdir, path

_running_mocks = []

def open_playback_window(master, mqtt_manager, state_manager, playback_engine):
    """
    Opens a window to configure and launch mock sensor devices.
    Uses shared state to store settings like device count and interval.
    """
    win = tk.Toplevel(master)
    win.title("Data Playback Devices")
    win.geometry("800x500")



    selected_file = state_manager.get("playback/file", "")

    listdir_files = [f for f in listdir("data") if f.endswith(".csv")]
    print("Available files:", listdir_files)
    if selected_file not in listdir_files:
        selected_file = listdir_files[0] if listdir_files else ""
    state_manager.set("playback/file", selected_file)


    tk.Label(win, text="Playback File").pack(pady=5)
    file_select = ttk.Combobox(win, values=listdir_files, textvariable=tk.StringVar(value=selected_file))
    file_select.pack(pady=15)
    def start_playback():
        stop_playback()
        try:
            file = path.join("data", file_select.get())
            state_manager.set("playback/file", file)
        except ValueError:
            tk.Label(win, text="Invalid file!").pack()
            return
        playback_engine.start()

    def stop_playback():
        playback_engine.stop()
        tk.Label(win, text="Stopped all playback mocks.").pack()

    def handle_pause():
        pause_text.set("Resume Playback" if pause_text.get() == "Pause Playback" else "Pause Playback")
        for device in playback_engine.devices.values():
            device.toggle_pause()

    pause_text = tk.StringVar(value="Pause Playback")
    tk.Button(win, text="Start Playback", command=start_playback).pack(pady=5)
    tk.Button(win, textvariable=pause_text,  command=handle_pause).pack(pady=5)
    tk.Button(win, text="Stop Playback", command=stop_playback).pack(pady=5)
