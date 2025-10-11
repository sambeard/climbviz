import os
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import pandas as pd
from matplotlib.collections import LineCollection
import numpy as np
import time


class DebugView(tk.Frame):
    def __init__(self, parent, config, mqtt, device_mgr, buffer, interaction_engine, analysis_engine, state):
        super().__init__(parent)
        self.config = config
        self.data_path = config.get("data_path", "data/")
        self.device_mgr = device_mgr
        self.buffer = buffer
        self.interaction_engine = interaction_engine
        self.analysis_engine = analysis_engine
        self.state = state

        self.feature = tk.StringVar(value=state.get("features/selected", config["features"][0]))
        self.offset = tk.DoubleVar(value=state.get("time_offset", 0.0))
        # For interactions
        self.interaction = tk.StringVar(value=state.get("interaction/active", list(interaction_engine.interactions.keys())[0]))
        # For analyses (new)
        self.analysis = tk.StringVar(value=state.get("analysis/active", list(analysis_engine.analyses.keys())[0]))

        # Mode toggle: either "Interaction" or "Analysis"
        self.mode = tk.StringVar(value="Interaction")
        # Filepicker dropdown variable (for analysis mode)
        self.selected_file = tk.StringVar(value="")

        self._build_layout()
        self._bind_state()

        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.ani = FuncAnimation(self.fig, self._update_plot, interval=200)

    def _bind_state(self):
        self.feature.trace_add("write", lambda *_: self.state.set("features/selected", self.feature.get()))
        self.offset.trace_add("write", lambda *_: self.state.set("time_offset", self.offset.get()))
        self.interaction.trace_add("write", lambda *_: self._on_interaction_change(self.interaction.get()))
        self.analysis.trace_add("write", lambda *_: self._on_analysis_change(self.analysis.get()))
        self.selected_file.trace_add("write", lambda *_: self._on_recording_change(self.selected_file.get()))
        # Force an initial write so the state is up-to-date
        for control in [self.feature, self.offset, self.interaction, self.analysis]:
            control.set(control.get())

    def _on_recording_change(self, file_name):
        full_file_path = os.path.join(self.data_path, file_name)
        self.analysis_engine.set_playback_buffer_name(full_file_path)
        if self.mode.get() == "Analysis":
            self.analysis_engine.render()

    def _on_interaction_change(self, interaction_name):
        self.state.set("interaction/active", interaction_name)
        self.interaction_engine.set_interaction(interaction_name)

    def _on_analysis_change(self, analysis_name):
        self.state.set("analysis/active", analysis_name)
        self.analysis_engine.set_analysis(analysis_name)
        self.analysis_engine.render()

    def _build_layout(self):
        self.control_frame = tk.Frame(self)
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        self.plot_frame = tk.Frame(self)
        self.plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._build_device_controls()
        self._build_feature_selector()
        # Insert the new mode toggle (Interaction / Analysis) and dynamic content area.
        self._build_mode_toggle()
        self._build_offset_input()
        self._build_calibration_controls()
        self._build_global_controls()

    def _build_device_controls(self):
        tk.Label(self.control_frame, text="Devices").pack(anchor="w")
        self.device_check_vars = {}
        self.device_check_frame = tk.Frame(self.control_frame)
        self.device_check_frame.pack(fill=tk.X)

    def _refresh_device_checkboxes(self):
        current_set = set(self.device_mgr.devices)
        known_set = set(self.device_check_vars.keys())

        if current_set == known_set:
            return

        for widget in self.device_check_frame.winfo_children():
            widget.destroy()

        self.device_check_vars.clear()
        selected_set = set(self.device_mgr.get_selected_devices())

        for dev in sorted(current_set):
            var = tk.BooleanVar(value=(dev in selected_set))
            chk = tk.Checkbutton(
                self.device_check_frame, text=dev, variable=var,
                command=lambda d=dev, v=var: self._on_toggle_device(d, v)
            )
            chk.pack(anchor="w")
            self.device_check_vars[dev] = var

    def _on_toggle_device(self, device_id, var):
        if var.get():
            self.device_mgr.selected.add(device_id)
        else:
            self.device_mgr.selected.discard(device_id)
        self.device_mgr._update_state()
        if self.mode.get() == "Analysis":
            self.analysis_engine.render()

    def _build_feature_selector(self):
        tk.Label(self.control_frame, text="Feature").pack(anchor="w")
        for feat in self.config["features"]:
            tk.Radiobutton(self.control_frame, text=feat, value=feat,
                           variable=self.feature).pack(anchor="w")

    def _build_mode_toggle(self):
        # Container for the mode toggle and dynamic content.
        self.mode_toggle_frame = tk.Frame(self.control_frame)
        self.mode_toggle_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Mode toggle label and buttons.
        tk.Label(self.mode_toggle_frame, text="Mode").pack(anchor="w")
        toggle_frame = tk.Frame(self.mode_toggle_frame)
        toggle_frame.pack(fill=tk.X)
        tk.Radiobutton(toggle_frame, text="Interaction", variable=self.mode, value="Interaction",
                       command=self._update_interaction_analysis_view).pack(side=tk.LEFT, anchor="w")
        tk.Radiobutton(toggle_frame, text="Analysis", variable=self.mode, value="Analysis",
                       command=self._update_interaction_analysis_view).pack(side=tk.LEFT, anchor="w")
        
        # Container for dynamic content.
        self.interaction_analysis_container = tk.Frame(self.mode_toggle_frame)
        self.interaction_analysis_container.pack(fill=tk.X, pady=(5, 0))
        # Build initial view based on mode.
        self._update_interaction_analysis_view()

    def _update_interaction_analysis_view(self):
        # Clear the dynamic container.
        for widget in self.interaction_analysis_container.winfo_children():
            widget.destroy()
        
        if self.mode.get() == "Interaction":
            self._build_interaction_content(self.interaction_analysis_container)
            self.interaction_engine.start_engine()
        else:  # Analysis mode
            self.interaction_engine.stop_engine()
            self._build_analysis_content(self.interaction_analysis_container)

    def _build_interaction_content(self, parent):
        tk.Label(parent, text="LED Interaction").pack(anchor="w")
        for mode_name in self.interaction_engine.interactions.keys():
            tk.Radiobutton(parent, text=mode_name, value=mode_name,
                           variable=self.interaction,
                           command=lambda: self._on_interaction_change(self.interaction.get())
                           ).pack(anchor="w")

    def _build_analysis_content(self, parent):
        # First, display the filepicker dropdown above the radio buttons.
        tk.Label(parent, text="Select File").pack(anchor="w")
        # File options can be extracted from the config; here we use a default list if none is provided.
        file_options = os.listdir(self.data_path)
        file_options = [f for f in os.listdir(self.data_path) if f.endswith('.csv')]
        self.selected_file.set(file_options[0])
        ttk.OptionMenu(parent, self.selected_file, file_options[0], *file_options).pack(fill=tk.X, pady=(0, 5))
        
        # Then list the available analyses as radio buttons.
        tk.Label(parent, text="Analysis Options").pack(anchor="w")
        for analysis_name in self.analysis_engine.analyses.keys():
            tk.Radiobutton(parent, text=analysis_name, value=analysis_name,
                           variable=self.analysis,
                           command=lambda: self._on_analysis_change(self.analysis.get())
                           ).pack(anchor="w")

    def _build_offset_input(self):
        tk.Label(self.control_frame, text="Time Offset (s)").pack(anchor="w")
        entry = tk.Scale(self.control_frame, variable=self.offset, from_=-3, to=3, resolution=0.1, orient=tk.HORIZONTAL)
        entry.pack(fill=tk.X)

    def _build_calibration_controls(self):
        tk.Label(self.control_frame, text="Calibration").pack(anchor="w", pady=(10, 2))
        tk.Checkbutton(self.control_frame, text="Auto-Calibrate",
                  command=lambda: self.device_mgr.toggle_auto_calibrate()).pack(fill=tk.X)
        tk.Button(self.control_frame, text="Manual Calibrate",
                  command=self.device_mgr.start_manual_calibration).pack(fill=tk.X)

    def _build_global_controls(self):
        tk.Label(self.control_frame, text="Global Device Commands").pack(anchor="w", pady=(10, 2))

        btns = [
            ("Identify Devices", "identify"),
            ("Start Devices", "start"),
            ("Stop Devices", "stop"),
            ("Calibrate All", "calibrate"),
            ("Sync Time", "sync"),
            ("Reset", "reset")
        ]

        for label, cmd in btns:
            tk.Button(self.control_frame, text=label,
                    command=lambda c=cmd: self.device_mgr.send_cmd(c)).pack(fill=tk.X, pady=1)

    def _update_plot(self, _):
        self._refresh_device_checkboxes()
        feature = self.feature.get()
        selected = self.device_mgr.get_selected_devices()

        self.ax.clear()
        if(self.mode.get() == "Analysis"):
            buf = self.analysis_engine.buffer
            if (buf):
                for dev in self.device_mgr.get_selected_devices():
                    if dev not in buf.devices:
                        continue
                    times, values = buf.get_features_with_times(dev, feature)
                    smoothed = pd.Series(index=times, data=values).rolling(window=5).mean()
                    if (feature == "theta" or feature == "phi"):
                        times_m, values_m = buf.get_features_with_times(dev, 'mag')
                        smoothed_mag = pd.Series(index=times_m, data=values_m).rolling(window=25).mean()
                        smoothed_mag[smoothed_mag<2.5]= pd.NA 
                        smoothed_mag = smoothed_mag.fillna(0) / 10
                        smoothed_mag[smoothed_mag >1] = pd.NA
                        smoothed_mag.fillna(1)
                        print(smoothed_mag)
                        points = np.vstack([smoothed.index, smoothed.values]).T.reshape(-1, 1, 2)
                        segments = np.concatenate([points[:-1], points[1:]], axis=1)
                        colors = string_to_rgba_array(dev, smoothed_mag.values)
                        print(colors)
                        lc = LineCollection(segments, linewidth=1, label=dev, colors=colors)
                        self.ax.add_collection(lc)
                    else:
                        self.ax.plot(smoothed, label=dev, alpha=0.6)
                    self.ax.plot()
        else:
            now = time.time()
            window = self.config.get("plot_window", 30)
            future = self.config.get("future_margin", 5)
            left = now - window
            right = now + future
            self.ax.axvline(x=now, color='red', linestyle='--', label='Now')


            for dev in selected:
                times, values = self.buffer.get_features_with_times(dev, feature)
                smoothed = pd.Series(index=times, data=values).rolling(window=5).mean()
                self.ax.plot(smoothed, label=dev, alpha=0.6)

            self.ax.set_xlim(left, right)
        self.ax.set_title(f"{'Live' if self.mode.get() == 'Interaction' else self.selected_file.get()} Feature: {feature}")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel(feature)
        if feature == "theta":
            self.ax.set_ylim(-1, 1)
        if feature == "phi":
            self.ax.set_ylim(0, 1)
        if feature == "mag":
            self.ax.set_ylim(-5, 60)
        if feature in ["y", "x", "z"]:
            self.ax.set_ylim(-50, 50)
        
        if selected:
            self.ax.legend(loc='upper left')

        self.canvas.draw()



def string_to_rgba_array(name, alphas):
    """
    Map a string deterministically to an RGB color via NumPy’s RNG,
    then return an (N×4) array where N = len(alphas), RGB is fixed per string
    and A comes from alphas.

    Parameters
    ----------
    name : str
        Any string to seed the color generator.
    alphas : array‑like of float
        Values in [0,1] to use as the alpha channel.

    Returns
    -------
    rgba : np.ndarray, shape (N,4)
        RGBA colors for each alpha.
    """
    # Derive a 32‑bit unsigned seed from the string
    seed = abs(hash(name)) % (2**32)
    rng = np.random.default_rng(seed)

    # Generate one (r,g,b)
    rgb = rng.random(3)  # three floats in [0,1)

    # Prepare the alpha array
    alphas = np.clip(np.asarray(alphas, dtype=float), 0.0, 1.0)

    # Stack into (N,4)
    rgba = np.column_stack([
        np.full_like(alphas, rgb[0]),
        np.full_like(alphas, rgb[1]),
        np.full_like(alphas, rgb[2]),
        alphas
    ])
    return rgba